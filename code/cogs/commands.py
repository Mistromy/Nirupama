import discord
from discord.ext import commands

from utils.logger import bot_log
import utils.ship 

class commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  
        
    @discord.slash_command(description="ask the 8ball a question")
    async def eightball(self, ctx, question: str):   
        await ctx.respond(f'-# "{question}"\n**Never!**')     
        await ctx.send_followup("Command Is Unfinished", ephemeral=True)
        bot_log(f"/eightball {question} ran by {ctx.author.name}")

    @discord.slash_command(description="analyze tone of provided text")
    async def tone(self, ctx, text: str):
        await ctx.respond(f'-# "{text}"\n`98%` **Passive Aggressive**')

    @discord.slash_command(description="check how compatible two users are")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        await ctx.defer()
        ship_percentage, log, ai_comment, image_path = await utils.ship.process_ship(user1, user2, ctx.guild)
        if image_path:
            file=discord.File(image_path, filename="ship_result.png")
            await ctx.respond(file=file, content=f"Ship Result: {ship_percentage}%\n\n> {ai_comment}")
        await ctx.respond(f" 💖 The compatibility between {user1.mention} and {user2.mention} is **{ship_percentage}%**!\n\n> {ai_comment}")
        bot_log(f"/ship {user1} {user2}.{log} ran by {ctx.author.name}")

# 5. THE HOOK (Spawn Actor)
# This is the MOST IMPORTANT part.
# When 'main.py' runs 'bot.load_extension()', it looks specifically for this function.
# If this is missing, the file is just text; it never gets added to the bot.
def setup(bot):
    bot.add_cog(commands(bot))