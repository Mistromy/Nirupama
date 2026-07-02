import discord
import re
from discord.ext import commands

from utils.logger import bot_log

honeypot_ids = {1522156724746715146, 1209888005829955624}

class HoneyPot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in honeypot_ids:
            await message.delete()
            await message.author.send("You have been banned for sending messages in the autoban channel.")
            await message.author.ban(reason="Suspected spambot", delete_message_seconds=86400)
            bot_log(f"Banned user {message.author}", level="info")
def setup(bot):
    bot.add_cog(HoneyPot(bot))