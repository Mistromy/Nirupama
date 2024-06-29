import discord
from config import PHOTOBOT_KEY
import random
import asyncio
import random as rand
import json
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import requests


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

user_message_counts = {}
bot = discord.Bot()


###--- 8Ball ---###
import requests

def get_8ball_answer(question, lucky=False):
    base_url = "https://www.eightballapi.com/api/biased"
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


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

#   --- NOT WORKING ---
    if message.content == "test":
        await message.respond("dawihkjs")


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


bot.run(PHOTOBOT_KEY)

#await ctx.followup.send(f"{above_text}\n\n{user_index+1}. <@{user_id}>: {user_score}\n\n{below_text}")