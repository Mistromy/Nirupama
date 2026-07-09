import discord 
from discord.ext import commands, tasks
import os
import json
import time
import aiohttp
from supabase import create_client

from utils.logger import bot_log

class websitestats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gist_id = "cdb82a1247ae6095f5d43098eb074dba"
        self.gist_token = os.getenv("STATS_GIST_TOKEN")

        self.cronitor_key = os.getenv("CRONITOR_API_KEY")
        self.monitor_key = "nirupama-heartbeat"
        
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        
        self.update_website_stats.start()

    def cog_unload(self):
        self.update_website_stats.cancel()

    async def get_total_tracked_messages(self):
        try:
            response = self.supabase.rpc("get_total_messages", {}).execute()
            return response.data if response.data is not None else 0
        except Exception as e:
            bot_log(f"Failed to fetch total messages from Supabase: {e}", level="error")
            return 0

    @tasks.loop(minutes=5)
    async def update_website_stats(self):
        cronitor_uptime = 100.0  # Default fallback if the API fetch fails

        # Fetch rolling 30-day metrics from Cronitor Aggregates API
        if self.cronitor_key:
            cronitor_url = f"https://cronitor.io/api/aggregates?monitor={self.monitor_key}&time=30d"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(cronitor_url, auth=aiohttp.BasicAuth(self.cronitor_key)) as resp:
                        if resp.status == 200:
                            cronitor_data = await resp.json()
                            monitor_metrics = cronitor_data.get("monitors", {}).get(self.monitor_key, {})
                            for env_key, env_data in monitor_metrics.items():
                                if isinstance(env_data, dict) and "uptime_percentage" in env_data:
                                    cronitor_uptime = env_data["uptime_percentage"]
                                    break
                        else:
                            bot_log(f"Failed to fetch Cronitor stats. Status: {resp.status}", level="error")
            except Exception as e:
                bot_log(f"Network error trying to fetch Cronitor metrics: {e}", level="error")

        stats = {
            "guild_count": len(self.bot.guilds),
            "user_count": sum(guild.member_count for guild in self.bot.guilds),
            "uptime": cronitor_uptime,
            "last_updated": int(time.time()),

            # Dynamically pull the database aggregate sum total
            "messages_tracked": await self.get_total_tracked_messages(),  
            # ------------------------------------------------------------------
            # FUTURE STATS — the website already has cards wired for these.
            # They render masked with a "soon" tag until a key appears here.
            # Uncomment and hook each one up to a real counter when ready, e.g.
            # a SELECT COUNT(*) from Supabase, or in-memory counters on the bot.
            # ------------------------------------------------------------------

            # "ships_calculated": self.bot.ship_counter,                    
            # "ai_replies": self.bot.ai_reply_counter,                                              
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
                    if response.status != 200:
                        err_response = await response.text()
                        bot_log(f"Failed to update Gist. Status: {response.status}. Error: {err_response}", level="error")
        except Exception as e:
            bot_log(f"Network error trying to update website stats Gist: {e}", level="error")

    @update_website_stats.before_loop
    async def before_update_website_stats(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(websitestats(bot))