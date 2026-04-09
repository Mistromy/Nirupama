import discord
from discord.ext import commands
import asyncio

# 1. IMPORTS (Dependencies)
# Just like "Add Component" or "Cast To".
# If you need your global variables, import ai_state.
# If you need to log things, import bot_log.
from utils.logger import bot_log
# from utils.ai_state import ai_state  <-- Uncomment if you need shared data

class MyNewCog(commands.Cog):
 
    def __init__(self, bot):
        self.bot = bot  # Save a reference to the "GameMode" (The Main Bot)
    
    @commands.Cog.listener()
    async def on_ready(self):
        # This is like 'Event BeginPlay' for this specific component.
        bot_log("MyNewCog is ready!", level="info")

    @discord.slash_command(description="Description of what this command does")
    async def joinvc(self, ctx):
        await ctx.defer()
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await ctx.respond(f"Joining {channel.name}!")
            await channel.connect()
            await ctx.followup.send("Joined the voice channel!")
            
            

# 5. THE HOOK (Spawn Actor)
# This is the MOST IMPORTANT part.
# When 'main.py' runs 'bot.load_extension()', it looks specifically for this function.
# If this is missing, the file is just text; it never gets added to the bot.
def setup(bot):
    bot.add_cog(MyNewCog(bot))