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
    serverlisttext = "".join([guild.name for guild in bot.guilds])
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))
    
    # Start the Discord Logging Worker
    setup_discord_logging(bot, LOG_CHANNEL_ID)
    
    bot_log(f"Logged in as {bot.user}", level="info")

@bot.event
async def on_guild_join(guild):
    serverlisttext = "".join([guild.name for guild in bot.guilds])
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))
    bot_log(f"Joined new guild: {guild.name} (ID: {guild.id})", level="info", important=True)

@bot.event
async def on_guild_remove(guild):
    serverlisttext = "".join([guild.name for guild in bot.guilds])
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))
    bot_log(f"Removed from guild: {guild.name} (ID: {guild.id})", level="info", important=True)

cogs_list = ['cogs.admin', 'cogs.commands', 'cogs.ai_core', 'cogs.tracking', 'cogs.uptime']
protected_cogs = ['cogs.admin', 'cogs.tracking', 'cogs.uptime']  # Always-on cogs

# Expose to bot for other cogs (e.g., admin) to use
bot.cogs_to_load = cogs_list
bot.protected_cogs = set(protected_cogs)
for cog in cogs_list:
    try:
        bot.load_extension(cog)
        bot_log(f"Loaded cog: {cog}", level="info")
    except Exception as e:
        bot_log(f"Failed to load {cog}: {e}", level="error", important=True)

if __name__ == "__main__":
    if not BOT_TOKEN:
        log.critical("BOT_TOKEN not found in .env file!")
        sys.exit(1)
        
    bot.run(BOT_TOKEN)
    sys.exit(bot.exit_code)