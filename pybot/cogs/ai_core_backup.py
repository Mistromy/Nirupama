import discord
from discord.ext import commands
import os
import time
import asyncio
from openai import OpenAI
import re

# Import your existing utilities
from utils.logger import bot_log
from utils.discord_helpers import send_smart_message
from data.ai_data import PERSONALITIES

class AICoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1",)
        self.personality = PERSONALITIES.get("Discord")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user in message.mentions:
            prompt = message.content
            user_content = [{"type": "text", "text": prompt}]
            
            # Check for images and add them to content
            has_images = False
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    user_content.append({"type": "image_url", "image_url": {"url": attachment.url}})
                    has_images = True
            
            # Choose model based on whether there are images
            if has_images:
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
            else:
                model = "llama-3.3-70b-versatile"
            
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self.personality},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=500,
                    temperature=1.6,
                )
                await send_smart_message(message.channel, response.choices[0].message.content, is_reply=True)
                return response.choices[0].message.content
            except Exception as e:
                bot_log(f"AI response error: {e}", level="error", important=True)
                await send_smart_message(message.channel, "Sorry, I encountered an error while processing your request.")
def setup(bot):
    bot.add_cog(AICoreCog(bot))