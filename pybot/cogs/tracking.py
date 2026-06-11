import discord
from discord.ext import commands
import time
from supabase import create_client
import os

from utils.logger import bot_log
from utils import levels

class tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        user_name = str(message.author)
        guild_id = message.guild.id
        # Round down to the nearest hour for the bucket
        bucket = (int(time.time()) // 3600) * 3600
        
        try:
            # This RPC now triggers the sync_user_totals() function in SQL automatically
            self.supabase.rpc("increment_message_activity", {
                "p_user_id": user_id,
                "p_guild_id": guild_id,
                "p_bucket_time": bucket,
                "p_user_name": user_name,
                "p_inc": 1
            }).execute()
        except Exception as e:
            bot_log(f"Activity log failed: {e}", level="error")

    async def getgraph(self, ctx, user: discord.Member = None, guild: discord.Guild = None, days: int = 7):
        await levels.getgraph(self.supabase, ctx, user, guild, days)

    async def messagecount(self, ctx, user: discord.Member = None, guild: discord.Guild = None):
        await levels.messagecount(self.supabase, ctx, user, guild)

    async def updatemessagecount(self, ctx, user: discord.Member = None, guild: discord.Guild = None, count: int = None):
        await levels.updatemessagecount(self.supabase, ctx, user, guild, count)

def setup(bot):
    bot.add_cog(tracker(bot))