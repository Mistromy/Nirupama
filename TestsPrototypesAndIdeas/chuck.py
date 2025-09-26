import requests
import discord
import asyncio
from config import PHOTOBOT_KEY

# Fetch a random chuck norris joke
async def get_joke():
    url = "https://api.chucknorris.io/jokes/random"
    response = requests.get(url)

    if response.status_code == 200:
        joke = response.json()["value"]
        return joke
    else:
        return "Error fetching joke"

# Set up the Discord client
intents = discord.Intents.default()
intents.members = True
intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    # Send a random joke every day
    while True:
        joke = await get_joke()
        for guild in client.guilds:
            for channel in guild.channels:
                if channel.id == 1205344852972146760:
                    await channel.send(joke)
        await asyncio.sleep(86400) # 1 day





# Replace the value below with your Discord bot token
client.run(PHOTOBOT_KEY)
