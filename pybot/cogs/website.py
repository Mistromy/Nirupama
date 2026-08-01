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
        self.ws_url = "ws://micro:6769/nirupama/live"
        self.session = None
        self.ws = None
        self.total_tracked_messages = 0
        self.connection_manager.start()
        self.gist_id = "cdb82a1247ae6095f5d43098eb074dba"
        self.gist_token = os.getenv("STATS_GIST_TOKEN")

        self.cronitor_key = os.getenv("CRONITOR_API_KEY")
        self.monitor_key = "nirupama-heartbeat"
        
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        
        self.update_website_stats.start()

    def cog_unload(self):
        self.update_website_stats.cancel()
        self.connection_manager.cancel()
    
    async def get_total_tracked_messages(self):
        try:
            response = self.supabase.rpc("get_total_messages", {}).execute()
            return response.data if response.data is not None else 0
        except Exception as e:
            bot_log(f"Failed to fetch total messages from Supabase: {e}", level="error")
            return 0
    total_tracked_messages = get_total_tracked_messages

    async def send_to_api(self, payload: dict):
        if self.ws is None or self.ws.closed:
            return

        try:
            await self.ws.send_json(payload)
        except Exception as e:
            bot_log(f"Failed to send data to WebSocket: {e}", level="error")
            self.ws = None


    @tasks.loop(seconds=5)
    async def connection_manager(self):
        if self.ws is not None and not self.ws.closed:
            return  # Already connected
        try:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()

            self.ws = await self.session.ws_connect(self.ws_url)
            bot_log("Connected to the live stats WebSocket.", level="info")
        except Exception as e:
            bot_log(f"Failed to connect to the live stats WebSocket: {e}", level="error")
            self.ws = None


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        self.total_tracked_messages += 1
        epoch_ms = int(message.created_at.timestamp() * 1000)
        payload = {
            "messages_tracked": self.total_tracked_messages,
            "epoch_ms": epoch_ms,
        }
        await self.send_to_api(payload)
        


    @tasks.loop(minutes=5)
    async def update_website_stats(self):
        cronitor_uptime = 100.0  # Default fallback if the API fetch fails
        self.total_tracked_messages = await self.get_total_tracked_messages()  # Fetch the total tracked messages from Supabase

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

        payload = {
            "messages_tracked": self.total_tracked_messages,
            "guild_count": len(self.bot.guilds),
            "user_count": sum(guild.member_count for guild in self.bot.guilds),
            "uptime": cronitor_uptime,
            "heartbeat_epoch_ms": int(time.time() * 1000),
            }
        await self.send_to_api(payload)
        payload["last_updated"] = int(time.time())
        gist_payload = {
            "description": "Live stats data for Nirupama website",
            "files": {
                "stats.json": {
                    "content": json.dumps(payload, indent=2)
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