import discord
from discord.ext import commands
import time
from supabase import create_client
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone
import io
import matplotlib.dates as mdates

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
        user_id = (user or ctx.author).id
        nick = (user or ctx.author).display_name # Fixes the "None" issue
        guild_obj = guild or ctx.guild
        
        try:
            # 1. Get the current Anchor (Total)
            stats = self.supabase.table("user_stats").select("total_messages")\
                .eq("user_id", user_id).eq("guild_id", guild_obj.id).maybe_single().execute()
            
            current_total = stats.data["total_messages"] if stats.data else 0

            # 2. Get the Deltas (Last 7 days = 168 hours)
            response = self.supabase.table("hourly_activity").select("bucket_time, message_count")\
                .eq("user_id", user_id).eq("guild_id", guild_obj.id)\
                .order("bucket_time", desc=True).limit(168).execute()

            rows = response.data
            if not rows:
                await ctx.respond("No activity recorded for this timeframe.", ephemeral=True)
                return

            # Reverse to get chronological order
            rows.reverse()
            
            # Calculate starting point for the graph
            period_sum = sum(r["message_count"] for r in rows)
            starting_total = current_total - period_sum

            # Prepare Data
            times = [datetime.fromtimestamp(r["bucket_time"]) for r in rows]
            deltas = [r["message_count"] for r in rows]
            
            # Cumulative growth logic: Start at 'starting_total', then add each delta
            y_values = [starting_total + sum(deltas[:i+1]) for i in range(len(deltas))]

            # --- Plotting ---
            fig, ax = plt.subplots(figsize=(12, 5))
            
            # Main Line
            ax.plot(times, y_values, color="#5865F2", linewidth=3, antialiased=True)
            # Area Fill
            ax.fill_between(times, y_values, starting_total, color="#5865F2", alpha=0.1)

            # Fix overlapping dates with AutoDateLocator
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
            plt.xticks(rotation=25, ha='right') # Rotate for readability

            ax.set_title(f"{nick}'s messages over time", pad=20, fontsize=14)
            ax.set_ylabel("Total Messages")
            
            # Aesthetics
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, axis='y', alpha=0.1)

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#2b2d31")
            buf.seek(0)
            plt.close(fig)

            await ctx.respond(file=discord.File(buf, "graph.png"))

        except Exception as e:
            bot_log(f"Graph Error: {e}", level="error")

    async def messagecount(self, ctx, user: discord.Member = None, guild: discord.Guild = None):
        user_id = user.id if user else ctx.author.id
        guild_id = (guild or ctx.guild).id
        
        # DEBUG LOG: Check exactly what IDs are being sent to Supabase
        bot_log(f"Fetching stats for User:{user_id} Guild:{guild_id}", level="info")
        
        user_obj = user or ctx.author
        guild_obj = guild or ctx.guild
        member_join_epoch = int(user_obj.joined_at.timestamp())

        try:
            # OPTIMIZED: Fetch total directly from user_stats (O(1) query)
            response = self.supabase.table("user_stats") \
                .select("total_messages") \
                .eq("user_id", user_id) \
                .eq("guild_id", guild_id) \
                .maybe_single().execute()
            
            if response.data:
                total = response.data["total_messages"]
                await ctx.respond(f"{user_obj.nick} has {total:,} messages in {guild_obj.name}")
            else:
                await ctx.respond("Database returned NO data. Check if your IDs match the Supabase table.", ephemeral=True)
                return

            # Check the earliest tracked data for this guild to see if they are a "Legacy" member
            guild_start_response = self.supabase.table("daily_activity").select("day_bucket")\
                .eq("guild_id", guild_id).order("day_bucket", desc=False).limit(1).execute()
            
            guild_added_epoch = guild_start_response.data[0]["day_bucket"] if guild_start_response.data else None

            if guild_added_epoch and member_join_epoch < guild_added_epoch:
                await ctx.send_followup(
                    f"⚠️ Note: You joined this server before the bot started tracking activity. "
                    f"Your total might be higher than what is shown here.", ephemeral=True
                )
        except Exception as e:
            bot_log(f"Query Error: {e}", level="error")
            await ctx.respond("Error retrieving message count.", ephemeral=True)

def setup(bot):
    bot.add_cog(tracker(bot))