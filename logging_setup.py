# logging_setup.py

import logging
import logging.handlers
import sys
import asyncio
import discord
from collections import deque
import io

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
    CYAN = "\x1b[36;20m"
    MAGENTA = "\x1b[35;20m"
    WHITE = "\x1b[37;20m"
    BOLD = "\x1b[1m"
    RESET = "\x1b[0m"

    # Color presets for easy use
    COLORS = {
        'grey': GREY,
        'yellow': YELLOW,
        'red': RED,
        'bold_red': BOLD_RED,
        'blue': BLUE,
        'green': GREEN,
        'cyan': CYAN,
        'magenta': MAGENTA,
        'white': WHITE,
        'bold': BOLD,
        'reset': RESET
    }

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
        try:
            log_entry = self.format(record)
            self.queue.put_nowait(log_entry)
        except Exception:
            self.handleError(record)

    async def send_long_message(self, channel, message, files=None):
        """Enhanced send_long_message function with proper message splitting and file attachment."""
        if not message and not files:
            return  # Skip empty messages

        if len(message) <= 2000:
            if files:
                await channel.send(message if message else None, files=files)
            else:
                await channel.send(message)
            return

        chunks = []
        current_chunk = ""
        in_code_block = False
        code_block_language = ""
        lines = message.split('\n')

        for line in lines:
            # Check for code block start/end
            if line.strip().startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_block_language = line.strip()[3:]
                else:
                    if line.strip() == '```':
                        in_code_block = False

            # If adding the new line exceeds the character limit
            if len(current_chunk) + len(line) + 1 > 2000:
                # If we are inside a code block, we must close it
                if in_code_block:
                    current_chunk += "\n```"

                if current_chunk.strip():  # Only add non-empty chunks
                    chunks.append(current_chunk)

                # Start the new chunk. If we were in a code block, re-open it.
                if in_code_block:
                    current_chunk = f"```{code_block_language}\n{line}"
                else:
                    current_chunk = line
            else:
                if current_chunk:
                    current_chunk += "\n" + line
                else:
                    current_chunk = line

        if current_chunk.strip():  # Only add non-empty final chunk
            chunks.append(current_chunk)

        # Send chunks, attaching files to the last chunk with text
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Skip empty chunks
                is_last_chunk = i == len(chunks) - 1
                chunk_files = files if (is_last_chunk and files) else None
                await channel.send(chunk, files=chunk_files)

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
                await self.send_long_message(channel, record)
            except asyncio.CancelledError:
                break  # Task was cancelled
            except discord.errors.Forbidden:
                print(f"ERROR: Bot does not have permission to send messages in channel {self.channel_id}.", file=sys.__stderr__)
                self.closed = True  # Stop trying
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


def bot_log(message: str, level=logging.INFO, command="general", color=None, **kwargs):
    """
    Enhanced log function that works as 'print with extra parameters'.

    Args:
        message: The message to log
        level: Logging level
        command: Command context
        color: Optional color for console output
        **kwargs: Additional parameters
    """
    logger = logging.getLogger("bot")
    extra = {'command': command}

    # Add color formatting if specified
    if color and hasattr(ColoredFormatter, 'COLORS') and color in ColoredFormatter.COLORS:
        formatted_message = f"{ColoredFormatter.COLORS[color]}{message}{ColoredFormatter.COLORS['reset']}"
        # Create a custom record for colored output
        record = logger.makeRecord(logger.name, level, "", 0, formatted_message, (), None, extra=extra)
        logger.handle(record)
    else:
        logger.log(level, message, extra=extra)


def setup_logging(bot: discord.Bot, channel_id: int, level=logging.INFO, discord_handler_level=logging.INFO, 
                 redirect_stdout=True, redirect_stderr=True, **kwargs):
    """
    Configures enhanced logging for the bot.
    """
    logger = logging.getLogger("bot")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console Handler with Colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # Discord Handler
    discord_handler = DiscordLogHandler(bot, channel_id, level=discord_handler_level)
    discord_formatter = logging.Formatter('```%(levelname)s [%(command)s] - %(asctime)s\n%(message)s\n```', 
                                        datefmt="%Y-%m-%d %H:%M:%S")
    discord_handler.setFormatter(discord_formatter)
    logger.addHandler(discord_handler)

    def enable_stream_redirects():
        """Function to redirect stdout and stderr to the logger."""
        if redirect_stdout:
            sys.stdout = StreamToLogger(logger, logging.INFO)
        if redirect_stderr:
            sys.stderr = StreamToLogger(logger, logging.ERROR)
        bot_log("Stdout and Stderr have been redirected to the logger.", command="setup", color="green")

    def start_discord_logging():
        """Function to start the Discord handler's worker task."""
        discord_handler.start_worker()

    return logger, discord_handler, bot_log, enable_stream_redirects, start_discord_logging
