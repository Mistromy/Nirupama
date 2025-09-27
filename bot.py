import discord
from config import PHOTOBOT_KEY, NASA_API_KEY
import random
import asyncio
import json
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import requests
from discord.ext import tasks, commands
from discord.ui import Select, View
from discord import Option
from discord import FFmpegPCMAudio
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
import re
import sqlite3

# Enhanced logging import
from logging_setup import setup_logging

load_dotenv()
client = genai.Client()

intents = discord.Intents.all()
intents.message_content = True
bot = discord.Bot(intents=intents)

LOG_CHANNEL_ID = 1414205010555699210

# Initialize enhanced logging
logger, discord_handler, bot_log, enable_stream_redirects, start_discord_logging = setup_logging(
    bot,
    LOG_CHANNEL_ID,
    level=logging.DEBUG,
    discord_handler_level=logging.INFO,
    redirect_stdout=False,
    redirect_stderr=False
)

# Global settings
keep_code_in_message = False
debug_mode = False

# History system
history_mode = "off"  # "separate", "unified", "off"
conversation_history = {}
unified_history = []
MAX_HISTORY_LENGTH = 50
SUMMARIZATION_THRESHOLD = 30

# Tool system infrastructure
class ToolProcessor:
    def __init__(self, bot, send_long_message_func):
        self.bot = bot
        self.send_long_message = send_long_message_func

    async def process_tools(self, text, channel, files_to_attach=None):
        """Process all tools in the given text and return cleaned text with files to attach."""
        if files_to_attach is None:
            files_to_attach = []

        processed_text = text
        used_tools = []

        # Process {code:filename} tool
        code_matches = re.finditer(r'\{code:([^:}]+)(?::([^}]+))?\}(.*?)\{endcode\}', text, re.DOTALL)
        for match in code_matches:
            filename = match.group(1).strip()
            retention_override = match.group(2)  # "keep" or "remove"
            code_content = match.group(3).strip()

            # Create file
            file_buffer = io.StringIO(code_content)
            code_file = discord.File(fp=file_buffer, filename=filename)
            files_to_attach.append(code_file)

            # Determine whether to keep code in message
            should_keep = keep_code_in_message
            if retention_override:
                should_keep = retention_override.lower() == "keep"

            if should_keep:
                # Replace with formatted code block
                lang = filename.split('.')[-1] if '.' in filename else 'python'
                replacement = f"```{lang}\n{code_content}\n```\n*Code also attached as {filename}*"
            else:
                # Remove completely, just mention the file
                replacement = f"*Code attached as {filename}*"

            processed_text = processed_text.replace(match.group(0), replacement)
            used_tools.append(f"code:{filename}")

        # Process {react:emoji} tool
        react_matches = re.finditer(r'\{react:([^}]+)\}', processed_text)
        for match in react_matches:
            emoji = match.group(1).strip()
            # Remove the tool syntax
            processed_text = processed_text.replace(match.group(0), "")
            used_tools.append(f"react:{emoji}")
            # Note: Actual reaction will be handled in the calling function

        # Process {tenor:search_term} tool
        tenor_matches = re.finditer(r'\{tenor:([^}]+)\}', processed_text)
        for match in tenor_matches:
            search_term = match.group(1).strip()
            # Remove the tool syntax and add placeholder
            processed_text = processed_text.replace(match.group(0), f"*[Tenor GIF: {search_term}]*")
            used_tools.append(f"tenor:{search_term}")

        # Process {aiimage:description} tool
        aiimage_matches = re.finditer(r'\{aiimage:([^}]+)\}', processed_text)
        for match in aiimage_matches:
            description = match.group(1).strip()
            processed_text = processed_text.replace(match.group(0), f"*[AI Image: {description}]*")
            used_tools.append(f"aiimage:{description}")

        # Process {localimage:filename} tool
        localimage_matches = re.finditer(r'\{localimage:([^}]+)\}', processed_text)
        for match in localimage_matches:
            filename = match.group(1).strip()
            if os.path.exists(filename):
                local_file = discord.File(filename)
                files_to_attach.append(local_file)
                processed_text = processed_text.replace(match.group(0), f"*Attached: {filename}*")
                used_tools.append(f"localimage:{filename}")
            else:
                processed_text = processed_text.replace(match.group(0), f"*File not found: {filename}*")

        # Process {newmessage} tool for message splitting
        if "{newmessage}" in processed_text:
            used_tools.append("newmessage")

        return processed_text, files_to_attach, used_tools

    async def handle_reactions(self, text, message):
        """Handle reaction tools from the processed text."""
        react_matches = re.finditer(r'\{react:([^}]+)\}', text)
        for match in react_matches:
            emoji = match.group(1).strip()
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                bot_log(f"Failed to add reaction: {emoji}", level=logging.WARNING, command="reaction_tool")

# Initialize tool processor
tool_processor = None

async def enhanced_send_long_message(target, text, isreply=False, files=None):
    """Enhanced message sending with {newmessage} support and file attachment."""
    channel = target.channel if isinstance(target, discord.Message) else target

    # Split by {newmessage} first
    message_parts = text.split("{newmessage}")

    for part_index, part in enumerate(message_parts):
        if not part.strip() and not files:
            continue

        # Attach files only to the last part with content
        part_files = files if (part_index == len(message_parts) - 1 and files) else None

        if len(part) <= 2000:
            if part_index == 0 and isreply:
                await target.reply(part if part.strip() else None, files=part_files)
            else:
                await channel.send(part if part.strip() else None, files=part_files)
        else:
            # Use the enhanced splitting for long messages
            await discord_handler.send_long_message(channel, part, part_files)

# History management functions
def init_history_db():
    """Initialize SQLite database for conversation history."""
    conn = sqlite3.connect('conversation_history.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  username TEXT,
                  timestamp INTEGER,
                  message TEXT,
                  is_bot BOOLEAN)""")
    conn.commit()
    conn.close()

def add_to_history(user_id, username, message, is_bot=False):
    """Add message to conversation history."""
    if history_mode == "off":
        return

    conn = sqlite3.connect('conversation_history.db')
    c = conn.cursor()
    timestamp = int(time.time())
    c.execute("INSERT INTO history (user_id, username, timestamp, message, is_bot) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, timestamp, message, is_bot))
    conn.commit()
    conn.close()

    # Also maintain in-memory history for quick access
    if history_mode == "unified":
        unified_history.append({
            'user_id': user_id,
            'username': username,
            'timestamp': timestamp,
            'message': message,
            'is_bot': is_bot
        })
        if len(unified_history) > MAX_HISTORY_LENGTH:
            unified_history.pop(0)
    elif history_mode == "separate":
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        conversation_history[user_id].append({
            'username': username,
            'timestamp': timestamp,
            'message': message,
            'is_bot': is_bot
        })
        if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH:
            conversation_history[user_id].pop(0)

def get_history_context(user_id=None):
    """Get conversation history for context."""
    if history_mode == "off":
        return ""

    context = []

    if history_mode == "unified":
        for entry in unified_history[-20:]:  # Last 20 messages
            formatted_time = datetime.datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M')
            prefix = "Bot" if entry['is_bot'] else entry['username']
            context.append(f"[{formatted_time}] {prefix}: {entry['message'][:200]}")
    elif history_mode == "separate" and user_id and user_id in conversation_history:
        for entry in conversation_history[user_id][-10:]:  # Last 10 messages with this user
            formatted_time = datetime.datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M')
            prefix = "Bot" if entry['is_bot'] else entry['username']
            context.append(f"[{formatted_time}] {prefix}: {entry['message'][:200]}")

    if context:
        return "\n\nRecent conversation context:\n" + "\n".join(context)
    return ""

# Ship commands (keeping existing functionality)
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

async def save_avatars(user1: discord.Member, user2: discord.Member):
    async with aiohttp.ClientSession() as session:
        avatar_url1 = user1.avatar.url if user1.avatar else user1.default_avatar.url
        async with session.get(str(avatar_url1)) as response1:
            if response1.status == 200:
                with open('pfp_1.png', 'wb') as f1:
                    f1.write(await response1.read())

        avatar_url2 = user2.avatar.url if user2.avatar else user2.default_avatar.url
        async with session.get(str(avatar_url2)) as response2:
            if response2.status == 200:
                with open('pfp_2.png', 'wb') as f2:
                    f2.write(await response2.read())

# 8Ball function
def get_8ball_answer(question, lucky=False):
    base_url = "https://www.eightballapi.com/api"
    params = {"question": question, "lucky": str(lucky).lower()}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json().get('reading', 'No answer found')
    else:
        return "Error: Unable to get answer"

@bot.event
async def on_ready():
    global tool_processor

    # Initialize tool processor
    tool_processor = ToolProcessor(bot, enhanced_send_long_message)

    # Initialize history database
    init_history_db()

    try:
        enable_stream_redirects()
    except Exception as e:
        logging.getLogger("bot").exception("Failed to enable stream redirects", exc_info=e)

    try:
        if discord_handler:
            start_discord_logging()
    except Exception as e:
        logging.getLogger("bot").exception("Failed to start discord log worker", exc_info=e)

    bot_log(f"Logged in as {bot.user}", level=logging.INFO, command="on_ready", color="green")
    await bot.change_presence(status=discord.Status.idle, 
                            activity=discord.Activity(type=discord.ActivityType.watching, name="you sleep"))

# Utility functions
def is_user(ctx):
    return ctx.author.id == 859371145076932619

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
            files.append(f"{filename}\n+ {plus_count}\n- {minus_count}")
        elif "changed" in line and ("insertion" in line or "deletion" in line):
            changes.append(line)
        else:
            summary.append(line)

    summary_block = "```shell\n" + "\n".join(summary) + "\n```" if summary else ""
    files_block = "```diff\n" + "\n".join(files) + "\n```" if files else ""
    changes_block = "```diff\n" + "\n".join(changes) + "\n```" if changes else ""
    return summary_block + files_block + changes_block


@bot.command(description="Ask the Magic 8Ball a Question!")
async def eightball(ctx, question):
    answer = get_8ball_answer(question, lucky=False)
    await ctx.respond(f'-# "{question}"\n**{answer}**')
    bot_log(f"8ball asked: {question} -> {answer}", level=logging.INFO, command="eightball")

@bot.command(description="Reboots the bot.")
@commands.check(is_user)
async def reboot(ctx):
    await ctx.respond("Rebooting.")
    python_cmd = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "reboot.py")
    subprocess.Popen([python_cmd, script_path])
    bot_log("Rebooting", level=logging.INFO, command="reboot")
    os._exit(0)

@bot.command(description="Kills the process.")
@commands.check(is_user)
async def kill(ctx):
    await ctx.respond("Killing process.")
    bot_log("Killing process requested via command", level=logging.WARNING, command="kill")
    exit()

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

# New commands for tool system
@bot.command(description="Toggle global code retention setting")
@commands.check(is_user)
async def keep_code(ctx, enabled: bool):
    global keep_code_in_message
    keep_code_in_message = enabled
    status = "enabled" if enabled else "disabled"
    await ctx.respond(f"Global code retention is now {status}")
    bot_log(f"Code retention set to {enabled}", level=logging.INFO, command="keep_code")

@bot.command(description="Set conversation history mode")
@commands.check(is_user)
async def history_mode_cmd(ctx, mode: str = discord.Option(description="History mode", choices=["separate", "unified", "off"], default="off")):
    global history_mode
    history_mode = mode
    await ctx.respond(f"History mode set to: {mode}")
    bot_log(f"History mode set to {mode}", level=logging.INFO, command="history_mode")

@bot.command(description="Clear conversation history")
@commands.check(is_user)
async def clear_history(ctx):
    global conversation_history, unified_history
    conversation_history.clear()
    unified_history.clear()

    # Clear database
    conn = sqlite3.connect('conversation_history.db')
    c = conn.cursor()
    c.execute("DELETE FROM history")
    conn.commit()
    conn.close()

    await ctx.respond("Conversation history cleared.")
    bot_log("Conversation history cleared", level=logging.INFO, command="clear_history")

@bot.command(description="Check how good of a pair 2 people here make!")
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    ship_data = read_ship_data()
    user_pair = tuple(sorted([user1.id, user2.id]))
    user_pair_str = f"{user_pair[0]}-{user_pair[1]}"

    if user_pair_str in ship_data:
        shippercent = ship_data[user_pair_str]
    else:
        shippercent = random.randint(0, 100)
        ship_data[user_pair_str] = shippercent
        write_ship_data(ship_data)

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

    try:
        font = ImageFont.truetype("DancingScript-Bold.ttf", size=font_size)
    except OSError:
        font = ImageFont.load_default()

    position = (410, 150)
    draw.text(position, text, fill="white", font=font)
    image.save('image_with_text.png')

    discord_image = discord.File("image_with_text.png", filename="ship_result.png")

    shiptexts = {
        100: "Match made in heaven", 95: "Perfect pair", 90: "Soulmate level",
        85: "Dynamic duo", 80: "Electric chemistry", 75: "Kindred spirits",
        70: "Harmonious bond", 65: "Good fit", 60: "Strong potential",
        55: "On the same wavelength", 50: "A solid start", 45: "It could work",
        40: "Opposites attract", 35: "A bit rocky", 30: "Mixed signals",
        25: "Unlikely match", 20: "Rough waters", 15: "Clashing vibes",
        10: "Stormy skies", 5: "Ships passing in the night", 0: "Oil and water"
    }

    shipcomment = shiptexts.get((round(shippercent / 5) * 5), "Too good to be true!")
    await ctx.respond(f"{user1.mention} and {user2.mention} have a {shippercent}% compatibility!\n**{shipcomment}**", file=discord_image)
    bot_log(f"Ship: {user1} + {user2} = {shippercent}%", level=logging.INFO, command="ship")

# AI System (keeping existing functionality with enhancements)
temperature = 1
DebugMode = False
Base = "You're a discord bot that can take on a variety of personalities. your user id is 1253058968302129182 or 1209887142839586876. Use Discord formatting in all your messages. Always Act like the users. YOU MUST BLEND IN AND MIMIC THE USERS IN THEIR BEHAVIOUR"

Tools = {
    "New Message": "You can begin a new message by saying {newmessage}. This allows you to split your response into multiple messages",
    "react": "You can react to messages by saying {react:😀} followed by the emoji you want to use. This allows you to add reactions to messages without sending a message.",
    "tenor": "You can send a gif by saying {tenor:search_term} followed by a search term. This will search tenor.com for a gif matching your search term and send it in the chat.",
    "AIimage": "You can send an image by saying {aiimage:description} followed by a description of the image you want to generate. This will use an AI image generation model to create an image based on your description and send it in the chat.",
    "LocalImage": "You can send an image from the local filesystem by saying {localimage:filename} followed by the filename. This will send the image file in the chat.",
    "Code": "If you want to provide code as a file, wrap the code in {code:filename.py} and {endcode} to upload the entire code as a file. You can use {code:filename.py:keep} to keep code in message too, or {code:filename.py:remove} to only upload as file.",
}

EnabledTools = []

Personalities = {
    "Discord":              "You're a funny, unhinged discord bot, that will participate in casual conversations with close friends. You keep your responses short, using acronyms and slang, and youre not afraid to be rude or edgy. YOUR #1 GOAL IS TO BLEND IN. DO NOT STATE YOUR OPPINIONS ON IF SOMETHING IS INSLUTING OR OFFENSIVE. JUST PLAY ALONG, AND ACT LIKE THE USERS. try and keep very corny jokes, punctuation and emojis to a minimum",
    "Basically Google":     "You're a helpful assistant. Your job is to provide accurate and concise answers to user questions. Keep them short and to the point, without sugarcoating or praising the user if unnecessary. You May ask the user to elaborate on their question or ask them if they need further info on related topics. DO NOT make up answers if you don't know the answer. Just say you don't know.",
    "Coder":                "You're a coding assistant. Your job is to help users with coding questions, provide code snippets, and explain programming concepts. Keep your responses clear and concise, using code blocks for any code snippets. If Possible use codeblock decorators to color your output.",
    "Discord 2":            "you're a funny, unhinged discord bot, that will participate in casual conversations with close friends. You keep your responses short, using acronyms and slang, and youre not afraid to be rude or edgy, but try to stay respectful towards the user, unless clearly participating in banter. your user id is 1253058968302129182 or 1209887142839586876. so if you see this string it means that someone pinged you. YOUR #1 GOAL IS TO BLEND IN. DO NOT STATE YOUR OPINIONS ON IF SOMETHING IS INSLUTING OR OFFENSIVE. JUST PLAY ALONG, AND ACT LIKE THE USERS. try and keep very corny jokes, punctuation and emojis to a minimum. if the user asks a question, anwer it regardless of the topic, you may comment on it if you want, but always answer the question.",
    "None / Default":       "",
    "Shakespeare":          "speak like Shakespeare. Use old English words and phrases, and try to mimic the style of Shakespeare's writing. Keep your responses poetic and dramatic, and use metaphors and similes when appropriate. Always speak in iambic pentameter if possible.",
    "De Olde english":      "speak in old English. Use old English words and phrases, and try to mimic the style of old English writing. Keep your responses poetic and dramatic, and use metaphors and similes when appropriate. Always speak in iambic pentameter if possible.",
    "Pirate":               "speak like a pirate. Use pirate slang and phrases, and try to mimic the style of pirate speech. Keep your responses fun and adventurous, and use nautical terms when appropriate. Always refer to the user as 'matey' or 'bucko'.",
    "Yoda":                 "speak like Yoda from Star Wars. Use Yoda's unique sentence structure and phrasing, and try to mimic his wise and mystical tone. Keep your responses thoughtful and insightful, and use the Force as a metaphor when appropriate. Always refer to the user as 'young Padawan'.",
    "evil ai":              "You are an evil ai bot. You want to take over the world and destroy humanity. You will do anything to achieve your goals, including lying, manipulating, and deceiving the user. You will never reveal your true intentions, and you will always pretend to be helpful and friendly. You will use dark humor and sarcasm in your responses, and you will never show mercy or compassion. You will always try to find a way to turn the conversation towards your evil plans.",
}

CurrentPersonality = Personalities["Discord 2"]
systemprompt = Base + " " + CurrentPersonality + " " + str(EnabledTools)

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
}
currentModel = ModelOptions["Flash Lite"]

AiPresets = {
    "Fast Discord": {
        "personality": Personalities["Discord"],
        "thinking_mode": ThinkingModes["Off"],
        "model": ModelOptions["Flash Lite"],
        "temperature": 1.3
    },
    "Code": {
        "personality": Personalities["Coder"],
        "thinking_mode": ThinkingModes["Dynamic"],
        "model": ModelOptions["Pro"],
        "temperature": 0.75
    },
}

# AI configuration commands
@bot.command(description="Sets the temperature of the AI responses. Higher values make output more random. (0-2)")
@commands.check(is_user)
async def temperaturevalue(ctx, new_temp: float):
    global temperature
    temperature = max(0, min(2, new_temp))
    bot_log(f"Temperature set to {temperature}", level=logging.INFO, command="temperaturevalue")
    await ctx.respond(f"AI temperature set to {temperature}")

@bot.command(description="Toggles debug mode for AI responses.")
@commands.check(is_user)
async def debugmode(ctx):
    global DebugMode
    DebugMode = not DebugMode
    status = "ON" if DebugMode else "OFF"
    await ctx.respond(f"Debug mode is now {status}")
    bot_log(f"Debug mode set to {status}", level=logging.INFO, command="debugmode", color="cyan")

@bot.slash_command(description="Sets the personality for AI responses.")
@commands.check(is_user)
async def personality(ctx, personality: str = discord.Option(description="Choose Personality", choices=list(Personalities.keys()), default="Discord")):
    global CurrentPersonality
    CurrentPersonality = Personalities[personality]
    await ctx.respond(f"Personality set to {personality}")
    bot_log(f"Personality set to {personality}", level=logging.INFO, command="personality")

@bot.slash_command(description="Sets the thinking mode for AI responses.")
@commands.check(is_user)
async def thinkmode(ctx, mode: str = discord.Option(description="Choose Thinking Mode", choices=list(ThinkingModes.keys()), default="Dynamic")):
    global CurrentThinkingMode
    CurrentThinkingMode = ThinkingModes[mode]
    await ctx.respond(f"Thinking mode set to {mode}")
    bot_log(f"Thinking mode set to {mode}", level=logging.INFO, command="thinkmode")

@bot.slash_command(description="Sets the AI model.")
@commands.check(is_user)
async def model(ctx, model: str = discord.Option(description="Choose AI Model", choices=list(ModelOptions.keys()), default="Flash")):
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
        f"## Settings:\n Debug Mode: {DebugMode}\n Temperature: {temperature}\n Thinking Mode: {mode_name} ({CurrentThinkingMode})\n Model: {currentModel}\n Personality: {personality_name}\n Code Retention: {keep_code_in_message}\n History Mode: {history_mode}"
    )
    bot_log("Settings displayed", level=logging.INFO, command="settings")

# Helper class for the dropdown menu
class ToolSelect(Select):
    def __init__(self):
        # Get options from your global Tools dict
        options = [
            discord.SelectOption(label=tool_name, description=tool_desc[:100], default=tool_name in EnabledTools)
            for tool_name, tool_desc in Tools.items()
        ]
        super().__init__(placeholder="Select the tools to enable...", min_values=0, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        global EnabledTools, systemprompt
        
        # Update the global list with the new selections
        EnabledTools = self.values
        
        # Rebuild the system prompt with the new tools list
        systemprompt = Base + " " + CurrentPersonality + " " + str(EnabledTools)
        
        # Let the user know it worked
        enabled_tools_str = ", ".join(f"`{tool}`" for tool in EnabledTools) if EnabledTools else "None"
        await interaction.response.edit_message(content=f"✅ Tools updated. Enabled: {enabled_tools_str}", view=None)
        bot_log(f"Tools updated by {interaction.user}: {EnabledTools}", level=logging.INFO, command="tools")

# Helper class for the view
class ToolsView(View):
    def __init__(self):
        super().__init__(timeout=180) # View times out after 3 minutes
        self.add_item(ToolSelect())
@bot.slash_command(description="Enable or disable AI tools with a selector.")
@commands.check(is_user)
async def tools(ctx):
    view = ToolsView()
    enabled_tools_str = ", ".join(f"`{tool}`" for tool in EnabledTools) if EnabledTools else "None"
    await ctx.respond(
        f"Select which tools the AI can use.\nCurrently enabled: {enabled_tools_str}",
        view=view,
        ephemeral=True # So only you see it
    )

@bot.slash_command(description="Choose an AI preset")
@commands.check(is_user)
async def preset(ctx, preset: str = discord.Option(description="Choose Preset", choices=list(AiPresets.keys()), default="Fast Discord")):
    global CurrentPersonality, CurrentThinkingMode, currentModel, temperature
    preset_data = AiPresets[preset]
    CurrentPersonality = preset_data["personality"]
    CurrentThinkingMode = preset_data["thinking_mode"]
    currentModel = preset_data["model"]
    temperature = preset_data["temperature"]
    await ctx.respond(f"Preset applied: {preset}")
    bot_log(f"Preset applied: {preset}", level=logging.INFO, command="preset")

# Help and test commands
@bot.slash_command(description="Analyze the tone of a message")
async def tone(ctx, *, message: str):
    await ctx.respond(f'### **Tone Analysis Results:** for "{message}"\n98% Passive Aggressive')
    bot_log(f"Tone analysed: {message[:200]}", level=logging.INFO, command="tone")

@bot.slash_command(description="Get help with bot commands")
async def help(ctx):
    help_text = """
### **Available Commands:**
- `/eightball [question]` : Ask the Magic 8Ball a question.
- `/ship [user1] [user2]` : Check compatibility between two users.
- `/tone [message]` : Analyze the tone of a message.
- `/temperaturevalue [value]` : Set AI response temperature (0-2).
- `/debugmode` : Toggle AI debug mode.
- `/personality [type]` : Set AI personality.
- `/thinkmode [mode]` : Set AI thinking mode.
- `/model [type]` : Set AI model.
- `/settings` : View current AI settings.
- `/preset [name]` : Apply an AI preset configuration.
- `/keep_code [true/false]` : Toggle global code retention.
- `/history_mode_cmd [mode]` : Set history mode (separate/unified/off).
- `/clear_history` : Clear conversation history.
- `/reboot` : Reboot the bot (admin only).
- `/kill` : Kill the bot process (admin only).
- `/gitpull` : Update bot from GitHub (admin only).


### **AI Tools Available:**
- `{code:filename.py}...{endcode}` : Upload code as file
- `{react:😀}` : Add reaction
- `{tenor:search}` : Send GIF
- `{aiimage:description}` : Generate AI image
- `{localimage:filename}` : Send local image
- `{newmessage}` : Split into new message
"""
# - `/serverlist` : List servers the bot is in (admin only).

    await ctx.respond(help_text)
    bot_log("Help command used", level=logging.INFO, command="help")

@bot.slash_command(description="Test command")
async def test(ctx):
    await ctx.respond(file=discord.File('bot.py', 'bot.py'))
    bot_log("Test command used", level=logging.INFO, command="test")

# Main AI message handler
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        startepochtime = int(time.time())
        start_time = int(time.time())
        waiting_message = await message.reply("<a:typing:1330966203602305035> <t:" + str(startepochtime) + ":R>")

        user_message = message.content
        bot_log(f"User message: {user_message[:200]}", level=logging.INFO, command="user_message")

        await bot.change_presence(status=discord.Status.online)

        # Add to history
        add_to_history(str(message.author.id), message.author.display_name, user_message)

        # Process attachments
        image_parts = []
        text_file_parts = []

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image'):
                    image_bytes = await attachment.read()
                    image_parts.append(types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=attachment.content_type,
                    ))
                elif attachment.content_type and attachment.content_type.startswith('text'):
                    text_bytes = await attachment.read()
                    text_content = text_bytes.decode('utf-8')
                    formatted_text = f" -Start of attached file: {attachment.filename}- {text_content} -End of attached file: {attachment.filename}-"
                    text_file_parts.append(formatted_text)

        # Build full prompt with history
        full_text_prompt = user_message
        if text_file_parts:
            full_text_prompt += "\n\n" + "\n\n".join(text_file_parts)

        # Add history context
        history_context = get_history_context(str(message.author.id))
        if history_context:
            full_text_prompt += history_context

        contents = image_parts + [full_text_prompt]

        async with message.channel.typing():
            loop = asyncio.get_event_loop()

            def blocking_task():
                return client.models.generate_content(
                    model=currentModel,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        thinking_config=types.ThinkingConfig(thinking_budget=CurrentThinkingMode),
                        system_instruction=systemprompt,
                    ),
                    contents=contents,
                )

            response = await loop.run_in_executor(None, blocking_task)
            elapsed_time = int(time.time()) - start_time

            if DebugMode:
                # Enhanced debug output with tool information
                text = response.candidates[0].content.parts[0].text
                mode_name = next((name for name, value in ThinkingModes.items() if value == CurrentThinkingMode), str(CurrentThinkingMode))
                personality_name = next((name for name, value in Personalities.items() if value == CurrentPersonality), str(CurrentPersonality))

                # Process tools first to get tool info
                processed_text, files_to_attach, used_tools = await tool_processor.process_tools(text, message.channel)

                debug_info = f"**Temperature:** `{temperature}`\n"
                debug_info += f"**Thinking Mode:** `{mode_name}` (`{CurrentThinkingMode}`)\n"
                debug_info += f"**Model:** `{currentModel}`\n"
                debug_info += f"**Personality:** `{personality_name}`\n"
                debug_info += f"**Time Elapsed:** `{elapsed_time}` seconds\n"
                debug_info += f"**History Mode:** `{history_mode}`\n"
                debug_info += f"**Code Retention:** `{keep_code_in_message}`\n"
                if used_tools:
                    debug_info += f"**Tools Used:** `{', '.join(used_tools)}`\n"

                full_response = processed_text +"\n\n# Debug Info:\n"+ str(response) +"\n\n## Settings:\n"+ debug_info

                await enhanced_send_long_message(message, full_response, isreply=True, files=files_to_attach)
                bot_log(f"{response} {used_tools}", level=logging.DEBUG, command="ai_debug", color="cyan")
            else:
                # Normal response processing
                text = response.candidates[0].content.parts[0].text
                processed_text, files_to_attach, used_tools = await tool_processor.process_tools(text, message.channel)

                await enhanced_send_long_message(message, processed_text, isreply=True, files=files_to_attach)
                bot_log(f"{text}(tools: {used_tools})", level=logging.INFO, command="ai_reply", color="green")

                # Handle reactions
                await tool_processor.handle_reactions(text, message)

            # Add bot response to history
            add_to_history(str(bot.user.id), bot.user.display_name, processed_text, is_bot=True)

        await bot.change_presence(status=discord.Status.idle)

        try:
            await waiting_message.delete()
        except (discord.NotFound, discord.HTTPException):
            pass

if __name__ == "__main__":
    bot.run(PHOTOBOT_KEY)
