import logging
import sys
import asyncio
import discord
from logging import Handler, LogRecord

# ANSI escape codes for colors
class Color:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """
    A custom formatter to add colors to log messages based on their level.
    """
    COLORS = {
        logging.DEBUG: Color.CYAN,
        logging.INFO: Color.GREEN,
        logging.WARNING: Color.YELLOW,
        logging.ERROR: Color.RED,
        logging.CRITICAL: Color.RED + Color.UNDERLINE,
    }

    def format(self, record):
        # Dynamically add the command to the record if it exists
        command_str = ""
        if hasattr(record, 'command') and record.command:
            command_str = f" [{record.command}]"
        
        # Base format string
        log_fmt = f"%(asctime)s [%(levelname)-8s]%(command_str)s %(message)s"
        
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        
        # Add our custom command string to the record for formatting
        record.command_str = command_str
        
        formatted_message = formatter.format(record)
        
        # Apply color
        log_color = self.COLORS.get(record.levelno, Color.WHITE)
        return f"{log_color}{formatted_message}{Color.RESET}"

class DiscordHandler(Handler):
    """
    A logging handler that sends logs to a Discord channel.
    This handler is asynchronous and uses an asyncio.Queue to avoid blocking.
    """
    def __init__(self, bot: discord.Bot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.queue = asyncio.Queue()

    def emit(self, record: LogRecord) -> None:
        """
        Formats the record and puts it into the queue.
        This method is thread-safe.
        """
        msg = self.format(record)
        # Discord has a 2000 character limit per message
        if len(msg) > 1990:
            msg = msg[:1990] + "..."
        self.queue.put_nowait(msg)

    async def worker(self):
        """The actual worker task that sends messages to Discord."""
        channel = await self.bot.fetch_channel(self.channel_id)
        if not channel:
            print(f"ERROR: Could not find log channel with ID {self.channel_id}", file=sys.__stderr__)
            return

        while True:
            try:
                message = await self.queue.get()
                if isinstance(channel, discord.TextChannel):
                    await channel.send(f"```log\n{message}\n```")
            except Exception as e:
                # Print errors to the original stderr in case the logging system itself is broken
                print(f"Error in Discord logger worker: {e}", file=sys.__stderr__)
            finally:
                self.queue.task_done()

class StreamToLogger:
    """
    A file-like object that redirects stream (stdout/stderr) output to a logger.
    """
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf: str):
        for line in buf.rstrip().splitlines():
            # Log each line separately
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        # This is needed for compatibility with the file-like object interface.
        pass

def setup_logging(bot: discord.Bot, channel_id: int, level=logging.INFO, discord_handler_level=logging.INFO, redirect_stdout=True, redirect_stderr=True, **kwargs):
    """
    Configures the entire logging system.
    """
    # 1. Get the root logger
    logger = logging.getLogger('bot')
    logger.setLevel(level)
    
    # 2. Setup Console Handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # 3. Setup Discord Handler
    discord_handler = DiscordHandler(bot, channel_id)
    discord_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(command)s] %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    discord_handler.setFormatter(discord_formatter)
    discord_handler.setLevel(discord_handler_level)
    logger.addHandler(discord_handler)

    # Store original streams
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # 4. Define function to enable stream redirection (called later in on_ready)
    def enable_stream_redirects():
        if redirect_stdout:
            sys.stdout = StreamToLogger(logger, logging.INFO)
        if redirect_stderr:
            sys.stderr = StreamToLogger(logger, logging.ERROR)
        logger.info("Stdout and Stderr have been redirected to the logger.")

    # 5. Define function to start the Discord worker (called later in on_ready)
    def start_discord_logging(loop):
        loop.create_task(discord_handler.worker())
        logger.info("Discord logging worker has been started.")

    # 6. Define the custom logging function
    def bot_log(message: str, level=logging.INFO, command: str = "general", extra_fields: dict = None):
        extra = {'command': command}
        if extra_fields:
            extra.update(extra_fields)
        logger.log(level, message, extra=extra)

    return logger, discord_handler, bot_log, enable_stream_redirects, start_discord_logging