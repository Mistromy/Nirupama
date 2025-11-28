from google import genai
from google.genai import types
import asyncio
from dotenv import load_dotenv
import os
from utils.logger import bot_log

load_dotenv()

client = genai.Client()

async def query_ai(prompt: str):
    response = await client.aio.models.generate_content(
    model = "gemini-2.0-flash",
    contents = prompt)
    return response.text