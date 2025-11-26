import logging
import asyncio
import sys
from utils.discord_helpers import send_smart_message

# --- 1. CUSTOM FORMATTER ---

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colors, timestamps, and line numbers.
    """
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    BLUE = "\x1b[34;20m"
    GREEN = "\x1b[32;20m"
    CYAN = "\x1b[36;20m"
    RESET = "\x1b[0m"

    COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        
        # If a category was passed in extra, use it, otherwise use 'SYS'
        cat = getattr(record, 'category', 'SYS')
        
        log_fmt = (
            f"{self.GREY}%(asctime)s{self.RESET} - "
            f"{color}%(levelname)-8s{self.RESET} - "
            # This will now correctly show the file that CALLED the log function
            f"{self.BLUE}[%(filename)s:%(lineno)d]{self.RESET} - "
            f"%(message)s"
        )
        
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

# --- 2. DISCORD HANDLER ---

class DiscordQueueHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.queue = asyncio.Queue()

    def emit(self, record):
        try:
            msg = self.format(record)
            self.queue.put_nowait(msg)
        except Exception:
            self.handleError(record)

async def discord_log_worker(bot, channel_id, queue_handler):
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    
    if not channel:
        print(f"Warning: Log Channel ID {channel_id} not found.")
        return
    
    bot_log(f"Connected to Log Channel: #{channel.name}", level="info")

    while not bot.is_closed():
        try:
            record = await queue_handler.queue.get()
            await send_smart_message(channel, f"```ini\n{record}\n```")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in log worker: {e}")

# --- 3. PUBLIC SETUP FUNCTIONS ---

def setup_logging():
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.INFO)
    logger.handlers = [] 

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    return logger

log = setup_logging()

def setup_discord_logging(bot, channel_id):
    queue_handler = DiscordQueueHandler()
    formatter = logging.Formatter('[%(levelname)s] [%(category)s] %(message)s')
    queue_handler.setFormatter(formatter)
    queue_handler.setLevel(logging.INFO)
    
    log.addHandler(queue_handler)
    
    bot.loop.create_task(discord_log_worker(bot, channel_id, queue_handler))

def bot_log(message, level="info", **kwargs):
    """
    Wrapper for logging that accepts 'category' and passes it to the formatter.
    """
    lvl = getattr(logging, level.upper(), logging.INFO)
    
    # We pass kwargs as 'extra' dict so the Formatter can see 'category'
    extra = kwargs
    if 'category' not in extra:
        extra['category'] = 'General'
    
    # CRITICAL FIX: stacklevel=2
    # This tells Python: "Don't report this line (inside bot_log). 
    # Report the line calling this function."
    log.log(lvl, message, extra=extra, stacklevel=2)