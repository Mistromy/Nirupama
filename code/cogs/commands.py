import discord
from discord.ext import commands

# 1. IMPORTS (Dependencies)
# Just like "Add Component" or "Cast To".
# If you need your global variables, import ai_state.
# If you need to log things, import bot_log.
from utils.logger import bot_log
# from utils.ai_state import ai_state  <-- Uncomment if you need shared data

class commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     bot_log("commands are ready!", level="info")

    @discord.slash_command(description="ask the 8ball a question")
    async def eightball(self, ctx, question: str):   
        await ctx.respond(f'-# "{question}"\n**Never!**')     
        await ctx.send_followup("Command Is Unfinished", ephemeral=True)
        bot_log(f"/eightball {question} ran by {ctx.author.name}")

    @discord.slash_command(description="analyze tone of provided text")
    async def tone(self, ctx, text: str):
        await ctx.respond(f'-# "{text}"\n`98%` **Passive Aggressive**')

# 5. THE HOOK (Spawn Actor)
# This is the MOST IMPORTANT part.
# When 'main.py' runs 'bot.load_extension()', it looks specifically for this function.
# If this is missing, the file is just text; it never gets added to the bot.
def setup(bot):
    bot.add_cog(commands(bot))