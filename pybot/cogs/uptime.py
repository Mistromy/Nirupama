import discord
from discord.ext import commands, tasks
import os
import cronitor

from utils.logger import bot_log

cronitor.api_key = os.getenv("CRONITOR_API_KEY")

class uptimecronitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.loopmonitor = cronitor.Monitor('nirupama-heartbeat')
        self.commandmonitor = cronitor.Monitor('nirupama-commands')
        self.send_uptime_ping.start()
        
    def cog_unload(self):
        self.send_uptime_ping.cancel()

    @tasks.loop(minutes=60)
    async def send_uptime_ping(self):
        self.loopmonitor.ping(state="run")
        try:
            # bot_log("Sent Cronitor heartbeat ping.", level="info")
            self.loopmonitor.ping(state="complete")
        except Exception as e:
            bot_log(f"Cronitor ping failed: {e}", level="error")
            self.loopmonitor.ping(state='fail', message=str(e))

    @send_uptime_ping.before_loop
    async def before_ping(self):
        await self.bot.wait_until_ready()

    async def runping(self):
        self.commandmonitor.ping(state="run")
    async def completeping(self):
        self.commandmonitor.ping(state="complete")
def setup(bot):
    bot.add_cog(uptimecronitor(bot))