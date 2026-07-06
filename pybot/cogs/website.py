import discord 
from discord.ext import commands, tasks
import os
import json
import aiohttp

from utils.logger import bot_log

class websitestats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gist_id = "cdb82a1247ae6095f5d43098eb074dba"
        self.gist_token = os.getenv("STATS_GIST_TOKEN")
        
        self.update_website_stats.start()

    def cog_unload(self):
        self.update_website_stats.cancel()

    @tasks.loop(minutes=5)
    async def update_website_stats(self):

        stats = {
            "guild_count": len(self.bot.guilds),
            "user_count": sum(guild.member_count for guild in self.bot.guilds)
        }

        gist_payload = {
            "description": "Live stats data for Nirupama website",
            "files": {
                "stats.json": {
                    "content": json.dumps(stats, indent=2)
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {self.gist_token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "Nirupama-Bot-Stats-Task" 
        }

        url = f"https://api.github.com/gists/{self.gist_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=gist_payload) as response:
                    if response.status == 200:
                        bot_log("Website stats successfully pushed to GitHub Gist.", level="info")
                    else:
                        err_response = await response.text()
                        bot_log(f"Failed to update Gist. Status: {response.status}. Error: {err_response}", level="error")
        except Exception as e:
            bot_log(f"Network error trying to update website stats Gist: {e}", level="error")

def setup(bot):
    bot.add_cog(websitestats(bot))