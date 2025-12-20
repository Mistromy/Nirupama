import discord
from discord.ext import commands
import random
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
            if ai_comment:
                await ctx.respond(file=file, content=f"Ship Result: {ship_percentage}%\n\n> {ai_comment}")
            else:
                await ctx.respond(file=file, content=f"Ship Result: {ship_percentage}%")
        # await ctx.respond(f" 💖 The compatibility between {user1.mention} and {user2.mention} is **{ship_percentage}%**!\n\n> {ai_comment}")
        bot_log(f"/ship {user1} {user2}.{log} ran by {ctx.author.name}")

    @discord.slash_command(description="Submit a feature request or suggestion / bug report")
    async def suggest(self, ctx, suggestion: str):
        with open("suggestions.md", "a") as f:
            f.write(f"- **{ctx.author.name}**: {suggestion}\n")
        await ctx.respond("Thank you for your suggestion! It has been recorded.", ephemeral=True)
        bot_log(f"Suggestion submitted by {ctx.author.name}: {suggestion}", level="info")

    @discord.slash_command(description="Search a word or phrase in a Dictionary")
    async def dictionary(self, ctx, term: str):
        # await ctx.respond(f"Searching definition for: **{term}**")
        await ctx.send_followup("Command Is Unfinished", ephemeral=True)
        bot_log(f"/dictionary {term} ran by {ctx.author.name}")

    @discord.slash_command(description="Roll a 6 sided dice")
    async def diceroll(self, ctx):
        result = random.randint(1, 6)
        await ctx.respond(f"🎲 You rolled a **{result}**!")
        bot_log(f"/roll rolled a {result} by {ctx.author.name}")

# 5. THE HOOK (Spawn Actor)
# This is the MOST IMPORTANT part.
# When 'main.py' runs 'bot.load_extension()', it looks specifically for this function.
# If this is missing, the file is just text; it never gets added to the bot.
def setup(bot):
    bot.add_cog(commands(bot))