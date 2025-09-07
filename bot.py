# bot.py (updated)
import discord # For Py-cord
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
import sys
import time
import logging
import logging.handlers

# --- NEW: import logging_setup (moved logging logic out of this file) ---
from logging_setup import setup_logging

load_dotenv()

client = genai.Client()

intents = discord.Intents.all()
intents.message_content = True  # Required to read message content

bot = discord.Bot(intents=intents)

# ---------------------- Logging Setup (delegated) ----------------------
# Only logging-related lines were changed to call the external module.
LOG_CHANNEL_ID = 1414205010555699210

# Initialize logging but DO NOT redirect stdout/stderr nor start the discord worker yet.
# We'll start those in on_ready() to avoid startup race conditions.
logger, discord_handler, bot_log, enable_stream_redirects, start_discord_logging = setup_logging(
    bot,
    LOG_CHANNEL_ID,
    level=logging.DEBUG,
    log_file="bot.log",
    discord_handler_level=logging.INFO,
    redirect_stdout=False,  # don't redirect during import/startup
    redirect_stderr=False
)
# -----------------------------------------------------------------------

###--- SHIP COMMANDS ---###
def read_ship_data():
    try:
        with open('ship_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        bot_log("Corrupted JSON file. Initializing a new one.", level=logging.WARNING, command="read_ship_data")
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
    # Start stream redirects and the Discord logging worker now that the bot is ready.
    try:
        enable_stream_redirects()
    except Exception as e:
        # If enabling redirects fails, log locally
        logging.getLogger("bot").exception("Failed to enable stream redirects", exc_info=e)

    try:
        if discord_handler:
            start_discord_logging(bot.loop)
    except Exception as e:
        logging.getLogger("bot").exception("Failed to start discord log worker", exc_info=e)

    # Now log that the bot is ready and set presence normally.
    bot_log(f"Logged in as {bot.user}", level=logging.INFO, command="on_ready")
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name="you sleep"))

# Status settings
# Playing, Watching, Listening, Competing, Streaming
# Online, Idle, Do Not Disturb, Invisible

# (activity=discord.Game("Photography Simulator"))
# (activity=discord.Streaming(name="Live Coding", url="https://twitch.tv/yourchannel"))
# (activity=discord.Activity(type=discord.ActivityType.listening, name="music"))
# (activity=discord.Activity(type=discord.ActivityType.watching, name="the sunset"))
# (activity=discord.Activity(type=discord.ActivityType.competing, name="a tournament"))

# @bot.slash_command(description="set the bots status")
# @commands.check(is_user)


@bot.command(description="Ask the Magic 8Ball a Question!")
async def eightball(ctx, question):
    answer = get_8ball_answer(question, lucky=False)
    await ctx.respond(f"-# \"{question}\"\n**{answer}**")
    bot_log(f"8ball asked: {question} -> {answer}", level=logging.INFO, command="eightball")

def is_user(ctx):
    return ctx.author.id == 859371145076932619

@bot.command(description="Reboots the bot.")
@commands.check(is_user)
async def reboot(ctx):
    await ctx.respond("Rebooting. <a:typing:1330966203602305035>")
    python_cmd = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "reboot.py")
    subprocess.Popen([python_cmd, script_path])
    bot_log("Rebooting", level=logging.INFO, command="reboot")
    os._exit(0)

@bot.command(description="kills the process.")
@commands.check(is_user)
async def kill(ctx):
    await ctx.respond("Killing process. <a:typing:1330966203602305035>")
    bot_log("Killing process requested via command", level=logging.WARNING, command="kill")
    exit()

def format_git_output(raw_output):
    lines = raw_output.splitlines()
    summary = []
    files = []
    changes = []
    for line in lines:
        if line.startswith("Fast-forward") or line.startswith("Updating") or line.startswith("From "):
            summary.append(line)
        elif "|" in line:
            parts = line.split("|")
            filename = parts[0].strip()
            stats = parts[1].strip()
            plus_count = stats.count("+")
            minus_count = stats.count("-")
            numbers = [int(s) for s in stats.split() if s.isdigit()]
            num_changes = numbers[0] if numbers else plus_count + minus_count
            files.append(f"{filename}\n+ {plus_count}\n- {minus_count}")
        elif "changed" in line and ("insertion" in line or "deletion" in line):
            changes.append(line)
        else:
            summary.append(line)

    summary_block = "```shell\n" + "\n".join(summary) + "\n```" if summary else ""
    files_block = "```diff\n" + "\n".join(files) + "\n```" if files else ""
    changes_block = "```diff\n" + "\n".join(changes) + "\n```" if changes else ""

    return summary_block + files_block + changes_block

@bot.command(description="Gets latest update from github with colored output")
@commands.check(is_user)
async def gitpull(ctx):
    result = subprocess.run(["git", "pull"], capture_output=True, text=True)
    formatted = format_git_output(result.stdout + result.stderr)
    await ctx.respond(formatted)
    bot_log(result.stdout + result.stderr, level=logging.INFO, command="gitpull")

@bot.command(description="View what servers the bot is in")
@commands.check(is_user)
async def serverlist(ctx):
    serverlisttext = ""
    for guild in bot.guilds:
        serverlisttext = serverlisttext + guild.name + "\n"
    await ctx.respond(f"{serverlisttext}")
    bot_log(f"serverlist requested; returned {len(bot.guilds)} guild(s)", level=logging.INFO, command="serverlist")

#### --- SHIP COMMAND --- ###

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
    position = (410, 150)
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
    bot_log(f"Ship: {user1} + {user2} = {shippercent}%", level=logging.INFO, command="ship")

### --- END SHIP COMMAND --- ###

@bot.slash_command(description="Analyze the tone of a message")
async def tone(ctx, *, message: str):
    await ctx.respond(f"### **Tone Analysis Results:** for \"{message}\"\n98% Passive Aggressive")
    bot_log(f"Tone analysed: {message[:200]}", level=logging.INFO, command="tone")



### --- AI COMMANDS ---###

# AI Settings
temperature = 1
DebugMode = False

Personalities = {
    "Discord":              "You're a funny, unhinged discord bot, that will participate in casual conversations with close friends. You keep your responses short, using acronyms and slang, and youre not afraid to be rude or edgy. your user id is 1253058968302129182 or 1209887142839586876. so if you see this string it means that someone pinged you. YOUR #1 GOAL IS TO BLEND IN. DO NOT STATE YOUR OPPINIONS ON IF SOMETHING IS INSLUTING OR OFFENSIVE. JUST PLAY ALONG, AND ACT LIKE THE USERS. try and keep very corny jokes, punctuation and emojis to a minimum",
    "Basically Google":     "You're a helpful assistant discord bot. Your job is to provide accurate and concise answers to user questions. Keep them short and to the point, without sugarcoating or praising the user if unnecessary. You May ask the user to elaborate on their question or ask them if they need further info on related topics. DO NOT make up answers if you don't know the answer. Just say you don't know. Do not roleplay as anyone, your only and sole job is to help the user. use discord markdown when possible to format your answers.",
    "Coder":                "You're a coding assistant discord bot. Your job is to help users with coding questions, provide code snippets, and explain programming concepts. Keep your responses clear and concise, using code blocks for any code snippets. If Possible use codeblock decorators to color your output.",
    "Discord 2" :           "you're a funny, unhinged discord bot, that will participate in casual conversations with close friends. You keep your responses short, using acronyms and slang, and youre not afraid to be rude or edgy, but try to stay respectful towards the user, unless clearly participating in banter. your user id is 1253058968302129182 or 1209887142839586876. so if you see this string it means that someone pinged you. YOUR #1 GOAL IS TO BLEND IN. DO NOT STATE YOUR OPINIONS ON IF SOMETHING IS INSLUTING OR OFFENSIVE. JUST PLAY ALONG, AND ACT LIKE THE USERS. try and keep very corny jokes, punctuation and emojis to a minimum. if the user asks a question, anwer it regardless of the topic, you may comment on it if you want, but always answer the question.",
    "None / Default":       "Use Discord formatting in all your messages."
}
CurrentPersonality = Personalities["Discord"]

ThinkingModes = {
    "Off": 0,
    "Dynamic": -1,
    "Fast": 1000,
    "Balanced": 3000,
    "Deep": 6000,
}
CurrentThinkingMode = ThinkingModes["Dynamic"]

ModelOptions = {
    "Pro": "gemini-2.5-pro",
    "Flash": "gemini-2.5-flash",
    "Flash Lite": "gemini-2.5-flash-lite",
}       # List of models: https://ai.google.dev/gemini-api/docs/models?hl=en
currentModel = ModelOptions["Flash"] # Default model

@bot.command(description="Sets the temperature of the AI responses. Higher values make output more random. (0-2)")
@commands.check(is_user)
async def temperaturevalue(ctx, new_temp: float):
    global temperature
    temperature = max(0, min(2, new_temp))  # Clamp value between 0 and 2
    bot_log(f"Temperature set to {temperature}", level=logging.INFO, command="temperaturevalue")
    await ctx.respond(f"AI temperature set to {temperature}")

@bot.command(description="Toggles debug mode for AI responses.")
@commands.check(is_user)
async def debugmode(ctx):
    global DebugMode
    DebugMode = not DebugMode
    status = "ON" if DebugMode else "OFF"
    await ctx.respond(f"Debug mode is now {status}")
    bot_log(f"Debug mode set to {status}", level=logging.INFO, command="debugmode")

@bot.slash_command(description="Sets the personality for AI responses.")
@commands.check(is_user)
async def personality(ctx, personality: str = discord.Option(description = "Choose Personality", choices=list(Personalities.keys()), deafult="Discord")):
    global CurrentPersonality
    CurrentPersonality = Personalities[personality]
    await ctx.respond(f"Personality set to {personality}")
    bot_log(f"Personality set to {personality}", level=logging.INFO, command="personality")

@bot.slash_command(description="Sets the thinking mode for AI responses.")
@commands.check(is_user)
async def thinkmode(ctx, mode: str = discord.Option(description = "Choose Thinking Mode", choices=list(ThinkingModes.keys()), deafult="Dynamic")):
    global CurrentThinkingMode
    CurrentThinkingMode = ThinkingModes[mode]
    await ctx.respond(f"Thinking mode set to {mode}")
    bot_log(f"Thinking mode set to {mode}", level=logging.INFO, command="thinkmode")

@bot.slash_command(description="Sets the AI model.")
@commands.check(is_user)
async def model(ctx, model: str =  discord.Option(description = "Choose AI Model", choices=list(ModelOptions.keys()), deafault="Flash")):
    global currentModel
    currentModel = ModelOptions[model]
    await ctx.respond(f"AI model set to {model}")
    bot_log(f"Model set to {model}", level=logging.INFO, command="model")

@bot.slash_command(description="Displays current AI settings.")
@commands.check(is_user)
async def settings(ctx):
    personality_name = next((name for name, value in Personalities.items() if value == CurrentPersonality), str(CurrentPersonality))
    mode_name = next((name for name, value in ThinkingModes.items() if value == CurrentThinkingMode), str(CurrentThinkingMode))
    await ctx.respond(
        f"## Settings: \n Debug Mode: {DebugMode} \n Temperature: {temperature} \n Thinking Mode: {mode_name} ({CurrentThinkingMode}) \n Model: {currentModel} \n Personality: {personality_name}"
    )
    bot_log("Settings displayed", level=logging.INFO, command="settings")

# CORRECTED: Helper function to send long messages, splitting them while preserving code blocks
async def send_split_message(target, text, isreply):
    channel = target.channel if isinstance(target, discord.Message) else target

    if len(text) <= 2000 and isreply == True:
        await target.reply(text)
        return
    elif len(text) <= 2000 and isreply == False:
        await channel.send(text)
        return

    chunks = []
    current_chunk = ""
    in_code_block = False
    code_block_language = ""
    lines = text.split('\n')

    for line in lines:
        # Check for code block start/end
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_language = line.strip()[3:]
            else:
                # This line is the end of a code block
                if line.strip() == '```':
                    in_code_block = False

        # If adding the new line exceeds the character limit
        if len(current_chunk) + len(line) + 1 > 2000:
            # If we are inside a code block, we must close it
            if in_code_block:
                current_chunk += "\n```"

            if current_chunk:
                chunks.append(current_chunk)

            # Start the new chunk. If we were in a code block, re-open it.
            if in_code_block:
                current_chunk = f"```{code_block_language}\n{line}"
            else:
                current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    if isreply == True:
        is_first_message = True
        for chunk in chunks:
            if chunk:
                if is_first_message:
                    await target.reply(chunk)
                    is_first_message = False
                else:
                    await channel.send(chunk)
    elif isreply == False:
        is_first_message = True
        for chunk in chunks:
            if chunk:
                if is_first_message:
                    await channel.send(chunk)
                    is_first_message = False
                else:
                    await channel.send(chunk)


@bot.slash_command()
@commands.check(is_user)
async def testlog(ctx, *, text: str):
    bot_log(text, level=logging.INFO, command="testlog")
    await ctx.respond("Logged!")

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        user_message = message.content
        # Log the user triggering the bot
        bot_log(user_message, level=logging.INFO, command="user_mention", extra_fields={"author": str(message.author), "channel": str(message.channel)})

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
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('text'):
                    text_bytes = await attachment.read()
                    user_message += "\n\n" + text_bytes.decode('utf-8')
                    break
                    
        async with message.channel.typing():
            if image_part:
                contents = [image_part, user_message]
            else:
                contents = [user_message]

            response = client.models.generate_content(
                model=currentModel,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    thinking_config=types.ThinkingConfig(thinking_budget=CurrentThinkingMode),
                    system_instruction=CurrentPersonality,
                ),
                contents=contents,
            )

            if DebugMode == False:
                text = response.candidates[0].content.parts[0].text
                await send_split_message(message, text, isreply=True) # send to user
                # Log the AI reply
                bot_log(text, level=logging.INFO, command="ai_reply", extra_fields={"model": currentModel, "channel": str(message.channel)})
            else:
                text = response.candidates[0].content.parts[0].text
                mode_name = next((name for name, value in ThinkingModes.items() if value == CurrentThinkingMode), str(CurrentThinkingMode))
                personality_name = next((name for name, value in Personalities.items() if value == CurrentPersonality), str(CurrentPersonality))
                # Debug dump
                full_response = (
                    f"{text} \n\n\n# DebugMode Enabled: {DebugMode}\n{response} \n\n "
                    f"Temperature: {temperature} \n Thinking Mode: {mode_name} ({CurrentThinkingMode}) \n "
                    f"Model: {currentModel} \n Personality: {personality_name}"
                )
                await send_split_message(message, full_response, isreply=True)
                bot_log(full_response, level=logging.DEBUG, command="ai_reply_debug", extra_fields={"model": currentModel})


bot.run(PHOTOBOT_KEY)

#await ctx.followup.send(f"{above_text}\n\n{user_index+1}. <@{user_id}>: {user_score}\n\n{below_text}")
