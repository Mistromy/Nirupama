import discord
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from datetime import datetime
import io
import numpy as np
from utils.logger import bot_log

# Configure matplotlib with modern Discord theme
plt.rcParams.update({
    "figure.facecolor": "#1e1f22",
    "axes.facecolor":   "#2c2f33",
    "axes.edgecolor":   "none",
    "axes.labelcolor":  "#dbdee1",
    "xtick.color":      "#949ba4",
    "ytick.color":      "#949ba4",
    "text.color":       "#dbdee1",
    "grid.color":       "#404249",
    "grid.linestyle":   ":",
    "grid.alpha":       0.3,
    "font.size":        9,
    "axes.titleweight": "bold",
    "figure.frameon":   False,
})

# Create a modern gradient colormap
colors_gradient = ['#404dff', '#5865f2', '#7c8df2']  # Modern blue gradient
n_bins = 256
cmap = LinearSegmentedColormap.from_list('modern_blue', colors_gradient, N=n_bins)


async def getgraph(supabase, ctx, user: discord.Member = None, guild: discord.Guild = None):
    """Generate and display a message activity graph for a user."""
    user_id = (user or ctx.author).id
    nick = (user or ctx.author).display_name  # Fixes the "None" issue
    guild_obj = guild or ctx.guild
    
    try:
        # 1. Get the current Anchor (Total)
        stats = supabase.table("user_stats").select("total_messages")\
            .eq("user_id", user_id).eq("guild_id", guild_obj.id).maybe_single().execute()
        
        current_total = stats.data["total_messages"] if stats.data else 0

        # 2. Get the Deltas (Last 7 days = 168 hours)
        response = supabase.table("hourly_activity").select("bucket_time, message_count")\
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

        # --- Plotting (Modern Styling) ---
        fig, ax = plt.subplots(figsize=(14, 3.2), dpi=110)
        fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.15)
        
        # Modern gradient fill with multiple layers for depth
        y_array = np.array(y_values)
        ax.fill_between(times, y_array, starting_total, color="#5865f2", alpha=0.15, label="Activity Zone")
        ax.fill_between(times, y_array, starting_total, color="#7c8df2", alpha=0.08)
        
        # Smooth main line with glow effect
        ax.plot(times, y_values, color="#5865f2", linewidth=2.5, antialiased=True, zorder=3)
        ax.plot(times, y_values, color="#404dff", linewidth=0.8, antialiased=True, alpha=0.4, zorder=2)

        # Fix overlapping dates with AutoDateLocator
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
        plt.xticks(rotation=25, ha='right', fontsize=8)  # Rotate for readability

        ax.set_title(f"{nick}'s messages over time", pad=15, fontsize=12, color="#dbdee1", loc='left')
        ax.set_ylabel("Total Messages", fontsize=9)
        
        # Modern aesthetics - clean and minimal
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#404249')
        ax.spines['bottom'].set_color('#404249')
        ax.spines['left'].set_linewidth(0.8)
        ax.spines['bottom'].set_linewidth(0.8)
        ax.grid(True, axis='y', alpha=0.2, linewidth=0.6)
        ax.set_axisbelow(True)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="#1e1f22", edgecolor="none")
        buf.seek(0)
        plt.close(fig)

        await ctx.respond(file=discord.File(buf, "graph.png"))

    except Exception as e:
        bot_log(f"Graph Error: {e}", level="error")


async def messagecount(supabase, ctx, user: discord.Member = None, guild: discord.Guild = None):
    """Get and display the total message count for a user."""
    user_id = user.id if user else ctx.author.id
    guild_id = (guild or ctx.guild).id
    
    # DEBUG LOG: Check exactly what IDs are being sent to Supabase
    bot_log(f"Fetching stats for User:{user_id} Guild:{guild_id}", level="info")
    
    user_obj = user or ctx.author
    guild_obj = guild or ctx.guild
    member_join_epoch = int(user_obj.joined_at.timestamp())

    try:
        # OPTIMIZED: Fetch total directly from user_stats (O(1) query)
        response = supabase.table("user_stats") \
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
        guild_start_response = supabase.table("daily_activity").select("day_bucket")\
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
