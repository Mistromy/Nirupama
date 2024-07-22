import discord
from config import PHOTOBOT_KEY, NASA_API_KEY
import random
import asyncio
import random as rand
import json
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import requests
from discord.ext import tasks
import datetime

# https://api.nasa.gov/planetary/apod?api_key=

intents = discord.Intents.all()
intents.message_content = True  # Required to read message content

bot = discord.Bot(intents=intents)

###--- SHIP COMMANDS ---###
def read_ship_data():
    try:
        with open('ship_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # Handle corrupted JSON file
        print("Corrupted JSON file. Initializing a new one.")
        return {}

def write_ship_data(data):
    with open('ship_data.json', 'w') as file:
        json.dump(data, file, indent=4)

# Function to fetch and save avatars using requests
async def save_avatars(user1: discord.Member, user2: discord.Member):
    async with aiohttp.ClientSession() as session:
        # Fetch and save avatar for user1
        avatar_url1 = user1.avatar.url if user1.avatar else user1.default_avatar.url
        async with session.get(str(avatar_url1)) as response1:
            if response1.status == 200:
                with open('pfp_1.png', 'wb') as f1:
                    f1.write(await response1.read())

        # Fetch and save avatar for user2
        avatar_url2 = user2.avatar.url if user2.avatar else user2.default_avatar.url
        async with session.get(str(avatar_url2)) as response2:
            if response2.status == 200:
                with open('pfp_2.png', 'wb') as f2:
                    f2.write(await response2.read())

###--- END SHIP COMMANDS ---###

###--- 8Ball ---###
import requests

def get_8ball_answer(question, lucky=False):
    base_url = "https://www.eightballapi.com/api"
    params = {
        "question": question,
        "lucky": str(lucky).lower()
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json().get('reading', 'No answer found')
    else:
        return "Error: Unable to get answer"
###--- END 8Ball ---###

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game("Photography Simulator"))

@bot.command(description="Throw those gypsies back to mexico!")
async def deport(ctx, arg):
    await ctx.respond(f'Omw, {arg} will be deported in 2-3 business days.')

@bot.command(description="Ask the Magic 8Ball a Question!")
async def eightball(ctx, question):

    answer = get_8ball_answer(question, lucky=False)
    await ctx.respond(f"{answer}")

@bot.command(description="Check how good of a pair 2 people here make!")
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    ship_data = read_ship_data()
    user_pair = tuple(sorted([user1.id, user2.id]))  # Use a tuple with sorted user IDs to ensure consistency
    user_pair_str = f"{user_pair[0]}-{user_pair[1]}"  # Convert the tuple to a string

    if user_pair_str in ship_data:
        shippercent = ship_data[user_pair_str]
    else:
        shippercent = random.randint(0, 100)
        ship_data[user_pair_str] = shippercent
        write_ship_data(ship_data)

    # Save avatars
    await save_avatars(user1, user2)
    
    pfp_1 = Image.open('pfp_1.png')
    pfp_2 = Image.open('pfp_2.png')
    bg = Image.open('bg.png')


    bg = bg.convert("RGBA")
    pfp_1 = pfp_1.convert("RGBA")
    pfp_2 = pfp_2.convert("RGBA")

    size = 200

    pfp_1 = pfp_1.resize((size, size))
    pfp_2 = pfp_2.resize((size, size))


    pos1 = (175, 100)
    pos2 = (660, 100)


    bg.paste(pfp_1, pos1, pfp_1)
    bg.paste(pfp_2, pos2, pfp_2)


    bg.save('result_image.png')

    image = Image.open("result_image.png")
    draw = ImageDraw.Draw(image)
    text = str(shippercent) + "%"
    font_size = 100
    font = ImageFont.truetype("DancingScript-Bold.ttf", size=font_size) 
    # If you have a TrueType font file (.ttf), you can load it like this:
    # font = ImageFont.truetype("arial.ttf", size=36)
    position = (410, 150)  # Top-left corner
    draw.text(position, text, fill="white", font=font)
    image.save('image_with_text.png')

    discord_image = discord.File("image_with_text.png", filename="ship_result.png")

    await ctx.respond(f"{user1.mention} and {user2.mention} have a {shippercent}% compatibility!", file=discord_image)


###--- Astronomy Picture Of The Day ---###


async def fetch_and_send_apod(channel):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}') as response:
            if response.status == 200:
                apod_data = await response.json()
                image_url = apod_data.get('url')
                explanation = apod_data.get('explanation')
                title = apod_data.get('title')
                if image_url:
                    embed = discord.Embed(title=title, description=explanation)
                    embed.set_image(url=image_url)
                    await channel.send(embed=embed)
            else:
                print(f"Failed to fetch APOD: {response.status}")

@bot.command(description="Send the NASA Astronomy Picture of the Day.")
async def apod(ctx):
    await fetch_and_send_apod(ctx.channel)

@tasks.loop(hours=24)
async def send_daily_apod():
    await bot.wait_until_ready()
    channel = bot.get_channel(1252034373746819207)
    if channel:
        await fetch_and_send_apod(channel)

@send_daily_apod.before_loop
async def before_send_daily_apod():
    # Calculate the time remaining until 12:00 GMT and sleep until then
    now = datetime.datetime.utcnow()
    target_time = datetime.datetime.combine(now.date(), datetime.time(hour=12))
    if now.time() > target_time.time():
        target_time += datetime.timedelta(days=1)
    await asyncio.sleep((target_time - now).total_seconds())

@bot.event
async def on_message(message):
    # if message.content.startswith("@Polish Ayumr"):
    if bot.user in message.mentions:
        await message.reply("Stfu, use commands bitch")

bot.run(PHOTOBOT_KEY)

#await ctx.followup.send(f"{above_text}\n\n{user_index+1}. <@{user_id}>: {user_score}\n\n{below_text}")