import discord
import os
import sys
from dotenv import load_dotenv
from utils.logger import log, bot_log, setup_discord_logging

load_dotenv()

# --- CONFIGURATION ---
LOG_CHANNEL_ID = 1414205010555699210
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

bot.exit_code = 0

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name="you sleep"))
    
    # Start the Discord Logging Worker
    setup_discord_logging(bot, LOG_CHANNEL_ID)
    
    bot_log(f"Logged in as {bot.user}", level="info")

# @bot.slash_command(description="Reboots the bot")
# async def reboot(ctx):
#     await ctx.respond("🔄 Rebooting system...", ephemeral=False)
#     bot_log(f"Reboot initiated by {ctx.author.name}", level="warning")
#     bot.exit_code = 2
#     await bot.close()

# @bot.slash_command(description="Kills the bot")
# async def kill(ctx):
#     await ctx.respond("Shutting down...", ephemeral=False)
#     bot_log(f"Shutdown initiated by {ctx.author.name}", level="critical")
#     bot.exit_code = 0
#     await bot.close()

# @bot.slash_command(description="restart specified cog")
# async def restart_cog(ctx, cog_name: str):
#     try:
#         bot.reload_extension(cog_name)
#         await ctx.respond(f"Restarted cog: {cog_name}", ephemeral=True)
#         bot_log(f"Cog {cog_name} restarted by {ctx.author.name}", level="info")
#     except Exception as e:
#         await ctx.respond(f"Failed to restart cog: {cog_name}. Error: {e}", ephemeral=True)
#         bot_log(f"Failed to restart cog {cog_name} by {ctx.author.name}: {e}", level="error")


cogs_list = ['cogs.ai_core', 'cogs.ai_settings', 'cogs.admin', 'cogs.commands']
for cog in cogs_list:
    try:
        bot.load_extension(cog)
        bot_log(f"Loaded cog: {cog}", level="info")
    except Exception as e:
        bot_log(f"Failed to load {cog}: {e}", level="error")

if __name__ == "__main__":
    if not BOT_TOKEN:
        log.critical("BOT_TOKEN not found in .env file!")
        sys.exit(1)
        
    bot.run(BOT_TOKEN)
    sys.exit(bot.exit_code)