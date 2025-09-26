import discord
from config import PHOTOBOT_KEY

intents = discord.Intents.all()
intents.message_content = True  # Required to read message content

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.content.startswith("ping"):
        print("kindaworked")
        await message.reply("pong")

bot.run(PHOTOBOT_KEY)
