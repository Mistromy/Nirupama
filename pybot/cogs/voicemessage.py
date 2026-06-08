import discord
from discord.ext import commands

from utils.logger import bot_log

class MyNewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.attachment.waveform:
            bot_log.info(f"voice message detected from {message.author} in {message.channel}")
            waveform = message.attachment.waveform
            

def setup(bot):
    bot.add_cog(MyNewCog(bot))