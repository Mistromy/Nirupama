import discord
from discord.ext import commands

# 1. IMPORTS (Dependencies)
# Just like "Add Component" or "Cast To".
# If you need your global variables, import ai_state.
# If you need to log things, import bot_log.
from utils.logger import bot_log
# from utils.ai_state import ai_state  <-- Uncomment if you need shared data

class admin(commands.Cog):
    """
    This is your 'Actor Component'.
    It holds a specific set of skills (Commands/Listeners).
    """

    # 2. CONSTRUCTOR (Construction Script)
    # This runs ONCE when the bot loads this file.
    def __init__(self, bot):
        self.bot = bot  # Save a reference to the "GameMode" (The Main Bot)
        
    # 3. EVENTS (Bind Event to Dispatcher)
    # This runs automatically when specific things happen.
    @commands.Cog.listener()
    async def on_ready(self):
        # This is like 'Event BeginPlay' for this specific component.
        bot_log("MyNewCog is ready!", level="info")

    # 4. COMMANDS (Custom Events)
    # This creates a Slash Command that users can trigger.
    @discord.slash_command(description="Description of what this command does")
    async def my_command(self, ctx):
        # ctx = Context. It's like 'Get Player Controller'. 
        # It holds info about WHO ran the command and WHERE.
        
        await ctx.respond("Hello from the new cog!")
        bot_log(f"Command executed by {ctx.author.name}")

# 5. THE HOOK (Spawn Actor)
# This is the MOST IMPORTANT part.
# When 'main.py' runs 'bot.load_extension()', it looks specifically for this function.
# If this is missing, the file is just text; it never gets added to the bot.
def setup(bot):
    bot.add_cog(admin(bot))