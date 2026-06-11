import discord
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone, timedelta
import io
from utils.logger import bot_log

# Configure matplotlib with a cleaner modern theme
plt.rcParams.update({
    "figure.facecolor": "#0e141b",
    "axes.facecolor":   "#111b24",
    "axes.edgecolor":   "#22303f",
    "axes.labelcolor":  "#dbe7f2",
    "xtick.color":      "#dbe7f2",
    "ytick.color":      "#dbe7f2",
    "text.color":       "#e5edf5",
    "grid.color":       "#2dd4bf",
    "grid.linestyle":   "-",
    "grid.alpha":       0.12,
    "font.size":        10,
    "axes.titleweight": "semibold",
})


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

        # Use timezone-aware datetimes so date boundaries (e.g., Jan 1) render consistently.
        times = [datetime.fromtimestamp(r["bucket_time"], tz=timezone.utc).astimezone() for r in rows]
        deltas = [r["message_count"] for r in rows]
        
        # Cumulative growth logic: Start at 'starting_total', then add each delta
        y_values = [starting_total + sum(deltas[:i+1]) for i in range(len(deltas))]

        # --- Plotting ---
        fig, ax = plt.subplots(figsize=(12, 3.6), constrained_layout=True)

        line_color = "#2dd4bf"
        glow_color = "#5eead4"
        accent_color = "#f59e0b"

        # Soft glow under the main line for a sleek look.
        ax.plot(times, y_values, color=glow_color, linewidth=7, alpha=0.08, solid_capstyle="round")
        ax.plot(times, y_values, color=line_color, linewidth=2.4, solid_capstyle="round")

        # Layered translucent fill to mimic a vertical gradient.
        fill_layers = [(0.35, 0.03), (0.65, 0.06), (1.0, 0.10)]
        for scale, alpha in fill_layers:
            scaled_values = [starting_total + ((y - starting_total) * scale) for y in y_values]
            ax.fill_between(times, scaled_values, starting_total, color="#14b8a6", alpha=alpha)

        # Highlight latest value.
        ax.scatter(times[-1], y_values[-1], s=42, color=accent_color, edgecolors="#fff7e0", linewidths=0.7, zorder=4)

        # Better date formatting across month/year boundaries.
        locator = mdates.AutoDateLocator(minticks=5, maxticks=9)
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        # Add a little horizontal padding so first/last labels and points are not clipped.
        x_min, x_max = min(times), max(times)
        x_pad = (x_max - x_min) * 0.02 if x_max > x_min else timedelta(hours=1)
        ax.set_xlim(x_min - x_pad, x_max + x_pad)

        ax.tick_params(axis="x", rotation=15)
        ax.set_title(f"{nick}'s Messages Over Time", pad=12, fontsize=12)
        ax.set_ylabel("Total Messages")

        # Aesthetics
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color("#2b3d4f")
        ax.spines['bottom'].set_color("#2b3d4f")
        ax.grid(True, axis='y')

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="#0e141b")
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

async def updatemessagecount(supabase, ctx, user: discord.Member = None, guild: discord.Guild = None, count: int = None):
    supabase.table("user_stats") \
        .update({"total_messages": count}) \
        .eq("user_id", user.id) \
        .eq("guild_id", guild.id) \
        .execute()
    await ctx.respond(f"{user.display_name}'s message count set to {count}")