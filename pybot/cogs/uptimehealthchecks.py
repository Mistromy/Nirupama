import discord
from discord.ext import commands, tasks
import requests
import os

from utils.logger import bot_log
healthcheck_url = os.getenv("HEALTHCHECKS_IO_URL")

class uptimehealthchecks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_uptime_ping.start()
        
    def cog_unload(self):
        self.send_uptime_ping.cancel()

    @tasks.loop(minutes=60)
    async def send_uptime_ping(self):
        try:
            requests.get(healthcheck_url, timeout=10)
        except requests.RequestException as e:
            bot_log(f"Uptime ping failed: {e}", level="error")
def setup(bot):
    bot.add_cog(uptimehealthchecks(bot))