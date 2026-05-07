import discord
from discord.ext import commands
import time
from supabase import create_client
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone
import io

from utils.logger import bot_log
plt.rcParams.update({
    "figure.facecolor": "#2b2d31",
    "axes.facecolor":   "#313338",
    "axes.edgecolor":   "#555",
    "axes.labelcolor":  "#dbdee1",
    "xtick.color":      "#dbdee1",
    "ytick.color":      "#dbdee1",
    "text.color":       "#dbdee1",
    "grid.color":       "#3f4147",
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.size":        10,
    "axes.titleweight": "semibold",
})

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

    async def getgraph(self, ctx, user: discord.Member = None, guild: discord.Guild = None):
        user_id = user.id if user else ctx.author.id
        nick = (user.nick or user.name) if user else (ctx.author.nick or ctx.author.name)
        guild = guild or ctx.guild
        guild_id = guild.id
        
        try:
            # RENAMED: message_activity -> hourly_activity
            response = self.supabase.table("hourly_activity").select(
                "bucket_time, message_count"
            ).eq("user_id", user_id).eq("guild_id", guild_id).order(
                "bucket_time", desc=True
            ).limit(168).execute()  # Last 7 days

            rows = response.data
            if not rows:
                await ctx.respond("No message data found for this user in the last 7 days.", ephemeral=True)
                return
            
            bucket_times = [r["bucket_time"] for r in rows]
            message_counts = [r["message_count"] for r in rows]
            bucket_times.reverse()
            message_counts.reverse()

            # Gap filling logic
            data_dict = {bucket_times[i]: message_counts[i] for i in range(len(bucket_times))}
            min_bucket, max_bucket = min(bucket_times), max(bucket_times)
            
            all_buckets, all_counts = [], []
            current_bucket = min_bucket
            while current_bucket <= max_bucket:
                all_buckets.append(current_bucket)
                all_counts.append(data_dict.get(current_bucket, 0))
                current_bucket += 3600 
            
            xs = [datetime.fromtimestamp(t) for t in all_buckets]
            ys = all_counts

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(xs, ys, color="#5865F2", linewidth=2)
            ax.fill_between(xs, ys, color="#5865F2", alpha=0.2)
            ax.set_title(f"{nick}'s Hourly Activity in {guild.name}")
            ax.set_ylabel("Messages per hour")
            ax.grid(True, alpha=0.3)

            for spine in ax.spines.values():
                spine.set_color("#555")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#2b2d31")
            buf.seek(0)
            plt.close(fig)

            await ctx.respond(file=discord.File(buf, "activity.png"))

        except Exception as e:
            bot_log(f"Graph failed: {e}", level="error")
            await ctx.respond("Error generating graph.", ephemeral=True)

    async def messagecount(self, ctx, user: discord.Member = None, guild: discord.Guild = None):
        user_id = user.id if user else ctx.author.id
        user_obj = user or ctx.author
        guild_obj = guild or ctx.guild
        guild_id = guild_obj.id
        member_join_epoch = int(user_obj.joined_at.timestamp())

        try:
            # OPTIMIZED: Fetch total directly from user_stats (O(1) query)
            stats_response = self.supabase.table("user_stats").select("total_messages")\
                .eq("user_id", user_id).eq("guild_id", guild_id).maybe_single().execute()
            
            total_messages = stats_response.data["total_messages"] if stats_response.data else 0

            # Check the earliest tracked data for this guild to see if they are a "Legacy" member
            guild_start_response = self.supabase.table("daily_activity").select("day_bucket")\
                .eq("guild_id", guild_id).order("day_bucket", desc=False).limit(1).execute()
            
            guild_added_epoch = guild_start_response.data[0]["day_bucket"] if guild_start_response.data else None

            await ctx.respond(f"User <@{user_id}> has sent a total of **{total_messages:,}** messages in **{guild_obj.name}**.")

            if guild_added_epoch and member_join_epoch < guild_added_epoch:
                await ctx.send_followup(
                    f"⚠️ Note: You joined this server before the bot started tracking activity. "
                    f"Your total might be higher than what is shown here.", ephemeral=True
                )
        except Exception as e:
            bot_log(f"Message count failed: {e}", level="error")
            await ctx.respond("Error retrieving message count.", ephemeral=True)

def setup(bot):
    bot.add_cog(tracker(bot))