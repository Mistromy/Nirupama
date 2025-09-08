# logging_setup.py
import logging
import logging.handlers
import sys
import asyncio
import discord
from collections import deque

class ColoredFormatter(logging.Formatter):
    """
    A custom log formatter that adds color to console output.
    """
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    BLUE = "\x1b[34;20m"
    GREEN = "\x1b[32;20m"
    RESET = "\x1b[0m"

    # Define the format for each log level, including custom fields
    FORMATS = {
        logging.DEBUG: f"{GREY}%(asctime)s - %(levelname)s - {BLUE}[%(command)s]{RESET} - %(message)s",
        logging.INFO: f"{GREEN}%(asctime)s - %(levelname)s - {BLUE}[%(command)s]{RESET} - %(message)s",
        logging.WARNING: f"{YELLOW}%(asctime)s - %(levelname)s - {BLUE}[%(command)s]{RESET} - %(message)s",
        logging.ERROR: f"{RED}%(asctime)s - %(levelname)s - {BLUE}[%(command)s]{RESET} - %(message)s",
        logging.CRITICAL: f"{BOLD_RED}%(asctime)s - %(levelname)s - {BLUE}[%(command)s]{RESET} - %(message)s",
    }

    def format(self, record):
        # Set default for custom field if not present
        if not hasattr(record, 'command'):
            record.command = 'general'
            
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

class DiscordLogHandler(logging.Handler):
    """
    A logging handler that sends logs to a Discord channel via an asyncio queue.
    """
    def __init__(self, bot: discord.Bot, channel_id: int, level=logging.NOTSET):
        super().__init__(level=level)
        self.bot = bot
        self.channel_id = channel_id
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.closed = False

    def emit(self, record):
        """Puts a formatted log message into the queue."""
        if self.closed:
            return
        # This method can be called from any thread, so we use thread-safe put_nowait
        try:
            log_entry = self.format(record)
            self.queue.put_nowait(log_entry)
        except Exception:
            self.handleError(record)

    async def _worker(self):
        """The background task that sends messages from the queue to Discord."""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"ERROR: Logging channel with ID {self.channel_id} not found.", file=sys.__stderr__)
            self.closed = True
            return

        while not (self.bot.is_closed() or self.closed):
            try:
                record = await self.queue.get()
                # Split messages longer than 2000 chars
                if len(record) > 2000:
                    # Preserve code blocks
                    if "```" in record:
                        parts = record.split("```")
                        # Send content outside code blocks
                        await channel.send(parts[0]) 
                        # Send content inside code block, splitting if necessary
                        code_block = parts[1]
                        for i in range(0, len(code_block), 1980):
                            await channel.send(f"```\n{code_block[i:i+1980]}\n```")
                        # Send any remaining content
                        if len(parts) > 2:
                            await channel.send(parts[2])
                    else: # Simple split for non-code messages
                        for i in range(0, len(record), 2000):
                            await channel.send(record[i:i+2000])
                else:
                    await channel.send(record)

            except asyncio.CancelledError:
                break # Task was cancelled
            except discord.errors.Forbidden:
                print(f"ERROR: Bot does not have permission to send messages in channel {self.channel_id}.", file=sys.__stderr__)
                self.closed = True # Stop trying
            except Exception as e:
                print(f"ERROR: Unhandled exception in Discord logging worker: {e}", file=sys.__stderr__)

    def start_worker(self):
        """Starts the background worker task if it's not already running."""
        if self.worker_task is None or self.worker_task.done():
            loop = asyncio.get_running_loop()
            self.worker_task = loop.create_task(self._worker())
            print("Discord logging worker started.")


class StreamToLogger:
    """
    A file-like object that redirects stdout/stderr to a logger instance.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

def setup_logging(bot: discord.Bot, channel_id: int, level=logging.INFO, discord_handler_level=logging.INFO, redirect_stdout=True, redirect_stderr=True, **kwargs):
    """
    Configures logging for the bot.
    """
    logger = logging.getLogger("bot")
    logger.setLevel(level)

    # --- Console Handler with Colors ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # --- Discord Handler (starts disabled, enabled later) ---
    discord_handler = DiscordLogHandler(bot, channel_id, level=discord_handler_level)
    # Simple formatter for Discord, as it handles its own formatting (e.g., code blocks)
    discord_formatter = logging.Formatter('```%(levelname)s [%(command)s] - %(asctime)s\n%(message)s\n```', datefmt="%Y-%m-%d %H:%M:%S")
    discord_handler.setFormatter(discord_formatter)
    logger.addHandler(discord_handler)

    def bot_log(message: str, level=logging.INFO, command="general", **kwargs):
        """Custom log function to easily add command context."""
        extra = {'command': command}
        logger.log(level, message, extra=extra)

    def enable_stream_redirects():
        """Function to redirect stdout and stderr to the logger."""
        if redirect_stdout:
            sys.stdout = StreamToLogger(logger, logging.INFO)
        if redirect_stderr:
            sys.stderr = StreamToLogger(logger, logging.ERROR)
        bot_log("Stdout and Stderr have been redirected to the logger.", command="setup")

    def start_discord_logging():
        """Function to start the Discord handler's worker task."""
        discord_handler.start_worker()

    # The setup function now returns the helper functions
    return logger, discord_handler, bot_log, enable_stream_redirects, start_discord_logging
