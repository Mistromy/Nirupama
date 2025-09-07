# logging_setup.py
"""
Logging subsystem for the bot.
- Create logger + rotating file + Rich console.
- Provide DiscordLogHandler that batches messages and posts to a channel.
- Provide bot_log(...) convenience function.
- Provide enable_stream_redirects() and start_discord_logging() to be called from on_ready().
"""

import asyncio
import logging
import logging.handlers
import sys
import io
import json
import datetime
from typing import Optional, Tuple, Callable

# put rich import at top for immediate visibility
try:
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _split_message(text: str, limit: int = 1800):
    """Split text into chunks under `limit`. Retains lines where possible."""
    if not text:
        return [""]
    parts = []
    current = []
    cur_len = 0
    for line in text.splitlines(keepends=True):
        if cur_len + len(line) > limit:
            if current:
                parts.append("".join(current))
                current = []
                cur_len = 0
            # If a single line is bigger than limit, split it directly
            while len(line) > limit:
                parts.append(line[:limit])
                line = line[limit:]
        current.append(line)
        cur_len += len(line)
    if current:
        parts.append("".join(current))
    return parts

# -------------------------
# Stream redirector
# -------------------------
class StreamToLogger(io.TextIOBase):
    """File-like object to redirect writes into a logger."""
    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        super().__init__()
        self.logger = logger
        self.level = level
        self._buffer = ""

    def write(self, s):
        if not s:
            return 0
        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if line:
                # Using logger.log so handlers are triggered
                self.logger.log(self.level, line)
        return len(s)

    def flush(self):
        if self._buffer:
            self.logger.log(self.level, self._buffer)
            self._buffer = ""

# -------------------------
# DiscordLogHandler
# -------------------------
class DiscordLogHandler(logging.Handler):
    """
    Logging handler that enqueues formatted log messages and a background
    coroutine sends them to a Discord channel in batches.
    """
    def __init__(self, bot_obj, channel_id: int, *,
                 level: int = logging.WARNING,
                 batch_interval: float = 1.0,
                 max_batch_chars: int = 1800):
        super().__init__(level=level)
        self.bot = bot_obj
        self.channel_id = channel_id
        self.batch_interval = batch_interval
        self.max_batch_chars = max_batch_chars
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._sending = False

        # default filter to avoid echoing discord internals
        def _filter(record):
            nm = (record.name or "")
            if nm.startswith("discord") or nm.startswith("websockets") or nm.startswith("aiohttp"):
                return False
            return True
        self.addFilter(_filter)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self._sending:
                # Avoid re-entrancy (logs emitted while we are sending)
                return
            msg = self.format(record)
            if not msg:
                return
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                loop.call_soon_threadsafe(self._queue.put_nowait, msg)
            else:
                # synchronous fallback if called prior to event loop creation
                asyncio.get_event_loop().run_until_complete(self._queue.put(msg))
        except Exception:
            self.handleError(record)

    async def _worker(self):
        # Wait for bot to be ready to guarantee fetch_channel works
        try:
            await self.bot.wait_until_ready()
        except Exception:
            # If bot has no wait_until_ready, ignore
            pass

        channel = None
        try:
            channel = await self.bot.fetch_channel(self.channel_id)
        except Exception:
            channel = None

        buffer = []
        while True:
            try:
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=self.batch_interval)
                    buffer.append(item)
                except asyncio.TimeoutError:
                    pass

                # Drain any other queued messages quickly
                while True:
                    try:
                        item = self._queue.get_nowait()
                        buffer.append(item)
                    except asyncio.QueueEmpty:
                        break

                if buffer:
                    combined = "\n\n".join(buffer)
                    parts = _split_message(combined, limit=self.max_batch_chars)

                    self._sending = True
                    try:
                        if channel is None:
                            try:
                                channel = await self.bot.fetch_channel(self.channel_id)
                            except Exception:
                                channel = self.bot.get_channel(self.channel_id)

                        if channel:
                            for part in parts:
                                try:
                                    # send as codeblock to preserve formatting/readability
                                    await channel.send(f"```{part}```")
                                except Exception as e:
                                    # If send fails, fallback to printing locally
                                    print("DiscordLogHandler send failed:", e, file=sys.stderr)
                        else:
                            print("DiscordLogHandler: no channel available to send logs.", file=sys.stderr)
                    finally:
                        self._sending = False
                    buffer = []
            except asyncio.CancelledError:
                break
            except Exception as e:
                print("DiscordLogHandler worker error:", e, file=sys.stderr)
                await asyncio.sleep(1.0)

    def start_worker(self, loop: asyncio.AbstractEventLoop):
        if self._worker_task is None:
            self._worker_task = loop.create_task(self._worker())

    def stop_worker(self):
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None

# --------------------------------------------------------------------
# Public API: setup_logging
# --------------------------------------------------------------------
def setup_logging(bot_obj,
                  discord_channel_id: Optional[int] = None,
                  *,
                  level: int = logging.DEBUG,
                  log_file: str = "bot.log",
                  max_bytes: int = 5_000_000,
                  backup_count: int = 3,
                  discord_handler_level: int = logging.INFO,
                  redirect_stdout: bool = False,
                  redirect_stderr: bool = False) -> Tuple[logging.Logger, Optional[DiscordLogHandler], Callable]:
    """
    Configure a logger named 'bot' and returns:
      (logger, discord_handler, bot_log)

    Note:
      - We do NOT redirect stdout/stderr by default. Call enable_stream_redirects() later
        (for example inside on_ready) to enable them after the bot finishes startup.
      - Call discord_handler.start_worker(loop) inside on_ready when the loop is ready.
    """
    root_logger = logging.getLogger("bot")
    root_logger.setLevel(level)

    # Remove existing handlers to keep idempotent
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root_logger.addHandler(fh)

    # Console handler (rich if available)
    if RICH_AVAILABLE:
        ch = RichHandler(rich_tracebacks=True, tracebacks_show_locals=False)
        ch.setFormatter(logging.Formatter("%(message)s"))
    else:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root_logger.addHandler(ch)

    # Quiet noisy libraries
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    discord_handler = None
    if discord_channel_id is not None:
        discord_handler = DiscordLogHandler(bot_obj, discord_channel_id, level=discord_handler_level)
        discord_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        root_logger.addHandler(discord_handler)
        # Do not start worker here — defer to on_ready to avoid loop race conditions

    # Do NOT redirect stdout/stderr during module import/startup unless redirect_xxx True
    # Provide helper functions below to enable redirection when safe.

    # bot_log function uses this logger
    def bot_log(message: str, *,
                level: int = logging.INFO,
                command: Optional[str] = None,
                extra_fields: Optional[dict] = None,
                send_immediate_to_channel = None,
                codeblock: bool = False):
        """
        Unified logging function. Use this in place of print().
        - timestamp and optional [command] tag are prepended.
        - logs to file + console + Discord handler (subject to its level/filtering).
        - If send_immediate_to_channel is provided (a discord.Channel-like object),
          the message will be scheduled for immediate send (split for length).
        """
        ts = datetime.datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        prefix = f"[{ts}]"
        if command:
            prefix += f" [{command}]"
        formatted = f"{prefix} {message}"
        if extra_fields:
            try:
                formatted = formatted + " | " + json.dumps(extra_fields, default=str)
            except Exception:
                # fallback
                formatted = formatted + " | " + str(extra_fields)

        root_logger.log(level, formatted)
        # immediate send is intentionally optional; to avoid excessive API calls by default
        if send_immediate_to_channel:
            async def _send_now():
                tgt = send_immediate_to_channel
                text = formatted
                if codeblock:
                    text = f"```{message}```"
                # We cannot import bot.send helper here — user will typically pass a channel object
                # Do naive send + splitting
                try:
                    parts = _split_message(text, limit=1800)
                    for p in parts:
                        await tgt.send(p)
                except Exception as e:
                    root_logger.exception("Failed to immediately send log to channel", exc_info=e)
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(_send_now())
                else:
                    asyncio.get_event_loop().run_until_complete(_send_now())
            except Exception:
                root_logger.exception("Failed to schedule immediate send", exc_info=True)

    # Functions to enable stream redirects and start the discord background worker
    def enable_stream_redirects():
        """Replace sys.stdout/sys.stderr to capture print() and errors. Call when safe (e.g. in on_ready)."""
        sys.stdout = StreamToLogger(logging.getLogger("bot.stdout"), logging.INFO)
        sys.stderr = StreamToLogger(logging.getLogger("bot.stderr"), logging.ERROR)

        # Hook uncaught exceptions
        def _excepthook(exc_type, exc, exc_tb):
            logging.getLogger("bot").exception("Uncaught exception", exc_info=(exc_type, exc, exc_tb))
        sys.excepthook = _excepthook

    def start_discord_logging(loop: asyncio.AbstractEventLoop):
        """Start the discord handler worker if a discord handler was created. Call from on_ready()."""
        if discord_handler is not None:
            discord_handler.start_worker(loop)

    return root_logger, discord_handler, bot_log, enable_stream_redirects, start_discord_logging
