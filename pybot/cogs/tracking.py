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
        bucket=(int(time.time()) // 3600) * 3600
        try:
            self.supabase.rpc("increment_message_activity", {
                "p_user_id": user_id,
                "p_guild_id": guild_id,
                "p_bucket_time": bucket,
                "p_user_name": user_name,
                "p_inc": 1
            }).execute()
        except Exception as e:
            bot_log(f"Activity log failed: {e}", level="error")

    @commands.slash_command(description="Generate activity graph for a user")
    async def getgraph(self, ctx, user: discord.Member = None, guild: discord.Guild = None):
        user_id = user.id if user else ctx.author.id
        guild = guild or ctx.guild
        guild_id = guild.id if guild else ctx.guild.id
        try:
            response = self.supabase.table("message_activity").select(
                "bucket_time, message_count"
            ).eq("user_id", user_id).eq("guild_id", guild_id).order(
                "bucket_time", desc=True
            ).limit(168).execute()  # last 7 days

            rows = response.data
            if not rows:
                await ctx.send_followup("No message data found for this user.", ephemeral=True)
                return
            
             # Extract and reverse
            bucket_times = [r["bucket_time"] for r in rows]
            message_counts = [r["message_count"] for r in rows]
            bucket_times.reverse()
            message_counts.reverse()

            # Fill gaps with zeros
            # Create a dictionary for fast lookup
            data_dict = {bucket_times[i]: message_counts[i] for i in range(len(bucket_times))}
            
            # Find the time range
            min_bucket = min(bucket_times)
            max_bucket = max(bucket_times)
            
            # Generate all hourly buckets in range
            all_buckets = []
            all_counts = []
            current_bucket = min_bucket
            while current_bucket <= max_bucket:
                all_buckets.append(current_bucket)
                all_counts.append(data_dict.get(current_bucket, 0))  # Use 0 if bucket not found
                current_bucket += 3600  # Add 1 hour
            
            # Use the complete data for plotting
            bucket_times = all_buckets
            message_counts = all_counts

            # Convert to datetime
            xs = [datetime.fromtimestamp(t) for t in bucket_times]
            ys = message_counts

            # Plot
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(xs, ys, color="#5865F2", linewidth=2)
            ax.fill_between(xs, ys, color="#5865F2", alpha=0.2)
            ax.set_title(f"{user}'s Activity in {guild}")
            ax.set_ylabel("Messages per hour")
            ax.grid(True, alpha=0.3)

            for spine in ax.spines.values():
                spine.set_color("#555")

            # Save to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#2b2d31")
            buf.seek(0)
            plt.close(fig)

            # Send
            await ctx.respond(file=discord.File(buf, "activity.png"))

        except Exception as e:
            bot_log(f"Graph failed: {e}", level="error")
            await ctx.respond("Error generating graph.", ephemeral=True)

    @commands.slash_command(description="Get your total message count")
    async def messagecount(self, ctx, user: discord.Member = None, guild: discord.Guild = None):
        user_id = user.id if user else ctx.author.id
        user = user or ctx.author
        guild_id = guild.id if guild else ctx.guild.id
        member_join_epoch = int(user.joined_at.timestamp())

        response = self.supabase.table("message_activity").select(
            "bucket_time"
        ).eq("guild_id", guild_id).order(
            "bucket_time"
        ).limit(1).execute()  # just get the first one
        rows = response.data
        if rows:
            guild_added_epoch = rows[0]["bucket_time"]  # Extract the timestamp
        else:
            guild_added_epoch = None


        try:
            response = self.supabase.table("message_activity").select(
                "message_count"
            ).eq("user_id", user_id).eq("guild_id", guild_id).execute()

            rows = response.data
            total_messages = sum(r["message_count"] for r in rows) if rows else 0

            await ctx.respond(f"User <@{user_id}> has sent a total of {total_messages} messages in {guild.name if guild else ctx.guild.name}.")
            member_has_updaetd_stats = False
            bot_log(f"Set member_has_updaetd_stats to False for debugging", level="info")
            if member_join_epoch < guild_added_epoch and member_has_updaetd_stats == False:
                await ctx.send_followup(f"Looks like you have joined this server before the bot started tracking levels. You can use the search feature to find your total message count. if you believe that the bot's message count is incorrect, you may request an update with updatemystats. a mod will then be able to assign you the correct amount of leves", ephemeral=True)
        except Exception as e:
            bot_log(f"Message count failed: {e}", level="error")
            await ctx.respond("Error retrieving message count.", ephemeral=True)
    
            

def setup(bot):
    bot.add_cog(tracker(bot))