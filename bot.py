import discord
from config import PHOTOBOT_KEY
import random
import asyncio
import os
import math
import threading
from discord import AllowedMentions
import random as rand
import json
from PIL import Image, ImageDraw, ImageFont
import aiohttp

def listen_for_console_input():
    while True:
        command = input()
        if command == "save":
            save_xp_to_file(user_message_counts)
            print("XP saved.")

threading.Thread(target=listen_for_console_input, daemon=True).start()

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

def save_xp_to_file(user_message_counts):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, 'xp_values.txt')
    with open(file_path, 'w') as file:
        for user_id, xp in user_message_counts.items():
            file.write(f"{user_id}:{xp}\n")

def load_xp_from_file():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, 'xp_values.txt')
    user_message_counts = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                user_id, xp = line.strip().split(':')
                user_message_counts[int(user_id)] = int(xp)
    except FileNotFoundError:
        pass  # File doesn't exist yet, which is fine
    return user_message_counts

user_message_counts = load_xp_from_file()  # Initialize with values from file
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game("Photography Simulator"))
    async def save_xp_periodically():
        await bot.wait_until_ready()
        while not bot.is_closed():
            save_xp_to_file(user_message_counts)
            await asyncio.sleep(200)  # Wait for  5 minutes

    bot.loop.create_task(save_xp_periodically())


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    user_name = message.author.name
    user_message_counts[user_id] = user_message_counts.get(user_id,  0) + random.randint(5,  15)

    # Calculate the user's level
    xp = user_message_counts[user_id]
    levelf =  0.3 * math.sqrt(xp)
    level = int(levelf)

    # Define the roles and their corresponding levels
    roles_levels = {
        10:  1207111158000263259,  # Level  10 role ID
        20:  1207111456659742730,  # Level  20 role ID
        30:  1207113962228023298,  # Level  30 role ID
        40:  1207113104492863578,  # Level  40 role ID
        60:  1207111046863785994,  # Level  60 role ID
        80:  1207103055103926302,  # Level  80 role ID
        90:  1207111660376948777,  # Level  90 role ID
        100:  1205492582512332810,  # Level  100 role ID
        120:  1207102955333882016,  # Level  120 role ID
        140:  1207112059796455434,  # Level  140 role ID
    }

    # Check if the user's level matches any of the roles
    for required_level, role_id in roles_levels.items():
        if required_level + 0.3 >= levelf >= required_level:
            # Fetch the role by ID
            role = discord.utils.get(message.guild.roles, id=role_id)
            if role is not None:
                # Assign the role to the user
                await message.author.add_roles(role)
                print(f"Role for level {required_level} has been assigned to {user_name}.")
            else:
                print(f"Role for level {required_level} not found.")

#   --- NOT WORKING ---
    if message.content == "test":
        await message.respond("dawihkjs")

    # Process commands after checking for role assignment
    # await bot.process_commands(message)

emoji_map = {
    0: "<:zero:1219277173014270052>",
    1: "<:jeden:1219277208929959937>",
    2: "<:dwa:1219277207550169129>",
    3: "<:trzy:1219277704277528586>",
    4: "<:cztery:1219277705300803680>",
    5: "<:pi:1219277706558963756>",
    6: "<:sze:1219277708467376128>",
    7: "<:siedem:1219277709579128843>",
    8: "<:osiem:1219277711172698113>",
    9: "<:dziewi:1219277712384856254>",
    10: "<:dziesi:1219277713525964860>"
}

@bot.command(description="Lets you see your level") 
async def level(ctx): 
    user_id = ctx.author.id
    xp = user_message_counts.get(user_id, 0)
    levelf = 0.3 * math.sqrt (xp)
    level = int(levelf)
    prcntf = (levelf - level) * 1000
    prcnt = (int(prcntf)) / 10
    fullbarsf = prcnt / 10
    fullbars = int(fullbarsf)
    bars = "<:dziesi:1219277713525964860>" * fullbars
    semibarf = prcnt - (fullbars*10)
    semibar = int(semibarf)
    selected_emoji = emoji_map[semibar]
    emptybarsno = 10 - fullbars -1
    emptybars = "<:zero:1219277173014270052>" * int(emptybarsno)
    await ctx.respond(f"You have {xp} xp \n That is level {level}! \n thats {prcnt}% of the way there to the next level\n{bars + selected_emoji + emptybars}")

# @bot.command(description="Counts the total number of messages sent by a user across all channels in the server.")
# async def count_all_messages(ctx, user: discord.Member):
#     message_count =  0
#     for channel in ctx.guild.channels:
#         if isinstance(channel, discord.TextChannel):  # Ensure we're only counting messages in text channels
#             async for message in channel.history(limit=None):  # Fetch all messages in the channel
#                 if message.author == user:
#                     message_count +=  1
#     await ctx.respond(f"{user.name} has sent {message_count} messages across all channels in this server.")

# @bot.command(description="Counts the total number of messages sent by a user in the current channel.")
# async def count_messages(ctx, user: discord.Member):
#     message_count =  0
#     async for message in ctx.channel.history(limit=None):
#         if message.author == user:
#             message_count +=  1
#     await ctx.respond(f"{user.name} has sent {message_count} messages in this channel.")

@bot.command(description="preview levels") 
async def levels(ctx): 
    await ctx.respond(f"# roles: \n <@&12071111580002635259> - level 10 \n <@&1207111456659742730> - level 20 \n <@&1207113962228023298> - level 30 \n <@&1207113104492863578> - level 40 \n <@&1207111046863785994> - level 60 \n <@&1207103055103926302> - level 80 \n <@&1207111660376948777> - level 90 \n <@&1205492582512332810> - level 100 \n <@&1207102955333882016>  - level 120 \n <@&1207112059796455434> - level 140")

@bot.command(description="Throw those gypsies back to mexico!")
async def deport(ctx, arg):
    await ctx.respond(f'Omw, {arg} will be deported in 2-3 business days.')

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


    pos1 = (150, 100)
    pos2 = (600, 100)


    bg.paste(pfp_1, pos1, pfp_1)
    bg.paste(pfp_2, pos2, pfp_2)


    bg.save('result_image.png')

    image = Image.open("result_image.png")
    draw = ImageDraw.Draw(image)
    text = str(shippercent) + "%"
    font_size = 100 
    font = ImageFont.load_default()  # Default font
    # If you have a TrueType font file (.ttf), you can load it like this:
    # font = ImageFont.truetype("arial.ttf", size=36)
    position = (350, 100)  # Top-left corner
    draw.text(position, text, fill="white", font=font, font_size=font_size)
    image.save('image_with_text.png')

    discord_image = discord.File("image_with_text.png", filename="ship_result.png")

    await ctx.respond(f"{user1.mention} and {user2.mention} have a {shippercent}% compatibility!", file=discord_image)



@bot.command(description="check leaderboard")
async def top(ctx):
    sorted_users = sorted(user_message_counts.items(), key=lambda item: item[1], reverse=True)
    top_ten_users = sorted_users[:10]
    top_ten_strings = [f"{index+1}. <@{user}>: {int(0.3 * math.sqrt (score))}" for index, (user, score) in enumerate(top_ten_users)]
    await ctx.respond("\n".join(top_ten_strings), allowed_mentions=AllowedMentions.none() )

@bot.command(description="Check position around the sender")
async def closest(ctx):
    user_id = str(ctx.author.id)  # Convert to string to ensure consistent type

    user_message_counts = load_xp_from_file()
    normalized_user_message_counts = {str(k): v for k, v in user_message_counts.items()}

    if user_id in normalized_user_message_counts:
        user_score = normalized_user_message_counts[user_id]
        sorted_users = sorted(normalized_user_message_counts.items(), key=lambda item: item[1], reverse=True)

        user_index = sorted_users.index((user_id, user_score))

        if user_index > 4:
            above_users = sorted_users[user_index - 5:user_index]
        else:
            above_users = sorted_users[max(0, user_index - 5):]

        below_users = sorted_users[user_index + 1:min(user_index + 6, len(sorted_users))]

        # Correctly calculate positions for above and below users
        above_positions = [user_index - i - 5 for i in range(len(above_users))]
        below_positions = [user_index + i + 1 for i in range(len(below_users))]

        above_text = "\n".join([f"{pos+1}. <@{user[0]}>: {user[1]}" for pos, user in zip(above_positions, above_users)])
        below_text = "\n".join([f"{pos+1}. <@{user[0]}>: {user[1]}" for pos, user in zip(below_positions, below_users)])

        await ctx.respond(content=f"{above_text}\n\n{user_index+1}. <@{user_id}>: {user_score}\n\n{below_text}", allowed_mentions=AllowedMentions.none())
    else:
        await ctx.respond(f"No data found for your ID.")

bot.run(PHOTOBOT_KEY)

#await ctx.followup.send(f"{above_text}\n\n{user_index+1}. <@{user_id}>: {user_score}\n\n{below_text}")