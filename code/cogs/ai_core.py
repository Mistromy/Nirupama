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

class AICoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1",)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user in message.mentions:
            prompt = message.content
            user_conent = [{"type": "text", "text": prompt}]
            if attachment in message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        user_conent.append({"type": "image_url", "image_url": {"url": attachment.url}})

                        try:
                            response = self.client.chat.completions.create(
                                model="meta-llama/llama-4-scout-17b-16e-instruct",
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant."},
                                    {"role": "user", "content": user_conent}
                                ],
                                max_tokens=500,
                                temperature=0.7,
                            )
                            await send_smart_message(message.channel, response.choices[0].message.content, is_reply=True)
                            return response.choices[0].message.content
                        except Exception as e:
                            bot_log(f"AI response error: {e}", level="error", important=True)
                            await send_smart_message(message.channel, "Sorry, I encountered an error while processing your request.")
            else:
                try:
                    response = self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": user_conent}
                        ],
                        max_tokens=500,
                        temperature=0.7,
                    )
                    await send_smart_message(message.channel, response.choices[0].message.content, is_reply=True)
                    return response.choices[0].message.content
                except Exception as e:
                    bot_log(f"AI response error: {e}", level="error", important=True)
                    await send_smart_message(message.channel, "Sorry, I encountered an error while processing your request.")
def setup(bot):
    bot.add_cog(AICoreCog(bot))