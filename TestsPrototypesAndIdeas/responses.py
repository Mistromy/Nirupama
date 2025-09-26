import discord
from discord.ext import commands
import time
import re
from config import PHOTOBOT_KEY

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

IGNORED_CHANNELS = [1206652473377292368, 1229790397430239272]

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        if message.channel.id not in IGNORED_CHANNELS:
            return

    async def send_message(input_str, *output_strs):
        if re.search(rf'\b{input_str}\b', message.content, re.IGNORECASE):
            time.sleep(0.15)
            for output_str in output_strs:
                await message.channel.send(output_str)
                time.sleep(0.2)

    async def send_response(input_str, output_str):
        if re.search(rf'\b{input_str}\b', message.content, re.IGNORECASE):
            time.sleep(0.15)
            await message.reply(output_str)

    await send_message("test", "testing", "testing1")
    await send_message("hello", "Hemlo!")
    await send_message("uwu", "weeb!")
    await send_message("call", "imagine being lonely")
    await send_message("ok", "If you dont have any actual thing to say then just shut up")
    await send_message("stfu", "You stop talking first. \n I'm programmed to respond to what you say.")
    await send_response("kys", "You first :)")
    await send_message("what", "<a:what:1092405139257692190> ")
    await send_response("daddy", "He's gone but im here for you")
    await send_message("Good", "<:frey:1177940675489185853>")
    await send_message("why?", "Ask bakoory")
    await send_message("i cant", "Skill issue")
    await send_message("i can't", "Skill issue")
    await send_message("nigger", "https://tenor.com/view/black-guy-maid-vibe-black-maid-dance-gif-26837778")
    await send_response("thanks for", "you're not welcome")
    await send_message("xd" ,"hilarious.")
    await send_message("1 sec", "hurry!")
    await send_message("want", "Keep dreaming boy!")
    await send_message("no", "why not")
    await send_message("yes", "no")
    await send_message("i wonder", "keep wondering")
    await send_response("<@1209887142839586876>", "im busy")

bot.run(PHOTOBOT_KEY)
