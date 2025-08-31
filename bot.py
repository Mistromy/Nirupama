import discord
from config import PHOTOBOT_KEY, NASA_API_KEY
import random
import asyncio
import json
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import requests
from discord.ext import tasks, commands
import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import wave
import io
from discord import FFmpegPCMAudio
import subprocess
from google import genai
from google.genai import types
load_dotenv()

client = genai.Client()

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
    await ctx.respond(f"-# \"{question}\"\n**{answer}**")

def is_user(ctx):
    return ctx.author.id == 859371145076932619

@bot.command(description="Reboots the bot.")
@commands.check(is_user)
async def reboot(ctx):
    await ctx.respond("Rebooting. <a:typing:1330966203602305035>")
    subprocess.run(["Nirupama\\reboot.py"])
    exit()

@bot.command(description="View what servers the bot is in")
@commands.check(is_user)
async def serverlist(ctx):
    serverlisttext = ""
    for guild in bot.guilds:
        serverlisttext = serverlisttext + guild.name + "\n"
    await ctx.respond(f"{serverlisttext}")

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

    shiptexts = {
        100: "Match made in heaven",
        95: "Perfect pair",
        90: "Soulmate level",
        85: "Dynamic duo",
        80: "Electric chemistry",
        75: "Kindred spirits",
        70: "Harmonious bond",
        65: "Good fit",
        60: "Strong potential",
        55: "On the same wavelength",
        50: "A solid start",
        45: "It could work",
        40: "Opposites attract",
        35: "A bit rocky",
        30: "Mixed signals",
        25: "Unlikely match",
        20: "Rough waters",
        15: "Clashing vibes",
        10: "Stormy skies",
        5: "Ships passing in the night",
        0: "Oil and water"
    }

    shipcomment = shiptexts.get((round(shippercent / 5) * 5), "Too good to be true!")
    await ctx.respond(f"{user1.mention} and {user2.mention} have a {shippercent}% compatibility! \n**{shipcomment}**", file=discord_image)

#AI Settings
temperature = 1
DebugMode = False

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if bot.user in message.mentions:
        user_message = message.content
        print(f"{user_message} \n \n")
        image_bytes = None
        image_part = None

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image'):
                    image_bytes = await attachment.read()
                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=attachment.content_type,
                    )
                    break
                    
        async with message.channel.typing():
            if image_part:
                contents = [image_part, user_message]
            else:
                contents = [user_message]

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="You're a funny, unhinged discord bot, that will participate in casual conversations with close friends. You keep your responses short, using acronyms and slang, and youre not afraid to be rude or edgy. your user id is 1253058968302129182 or 1209887142839586876. so if you see this string it means that someone pinged you. ",
                ),
                contents=contents, 
            )
            print(response)
            if DebugMode == False:
                text = response.candidates[0].content.parts[0].text
                await message.reply(text)
            else:
                await message.reply(str(response))


bot.run(PHOTOBOT_KEY)

#await ctx.followup.send(f"{above_text}\n\n{user_index+1}. <@{user_id}>: {user_score}\n\n{below_text}")
