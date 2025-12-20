from openai import OpenAI
import asyncio
from dotenv import load_dotenv
import os
from utils.logger import bot_log

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

async def query_ai(prompt: str):
    response = await client.chat.completions.create(
    model = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    messages = prompt)
    return response.text