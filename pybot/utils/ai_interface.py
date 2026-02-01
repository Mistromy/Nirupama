from openai import OpenAI
import asyncio
from dotenv import load_dotenv
import os
from utils.logger import bot_log

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

async def query_ai(prompt: str):
    print(prompt)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": prompt}]))
    if response:
        return response.choices[0].message.content
    else:
        return None