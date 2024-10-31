import discord
import wave
import io
import requests
from openai import OpenAI
from config import PHOTOBOT_KEY
from discord import FFmpegPCMAudio
import asyncio
from pathlib import Path 

client = OpenAI()


intents = discord.Intents.all()
intents.message_content = True  # Required to read message content

# bot = discord.Bot(intents=intents)

# @bot.command()
# async def join(ctx):
#     if ctx.author.voice is None:
#         await ctx.respond("You need to join a voice channel first.")
#         return

#     channel = ctx.author.voice.channel
#     if ctx.voice_client is not None:
#         await ctx.voice_client.move_to(channel)
#     else:
#         await channel.connect()
#     await ctx.respond(f"Joined {channel}")

# @bot.command()
# async def leave(ctx):
#     if ctx.voice_client is None:
#         await ctx.respond("I am not in a voice channel.")
#     else:
#         await ctx.voice_client.disconnect()
#         await ctx.respond("Disconnected")

    
def AiProcess():
  audio_file= open("audio.mp3", "rb")
  transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
  )
  print(transcription.text)
  

  
  response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": "Answer with short accurate answers. always answer in english, regardless of the language in which the question was asked"},
      {"role": "user", "content": "transcription.text"}
    ]
  )
  
  
  print(response)
  response_text = response.choices[0].message.content
  
  peech_file_path = Path(__file__).parent / "speech.mp3"
  response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=response_text
  )
  
  output_file_path = "output.mp3"
  
  with open(output_file_path, "wb") as file:
      file.write(response.content)
  

# bot.run(PHOTOBOT_KEY)