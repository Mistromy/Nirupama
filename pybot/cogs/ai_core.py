import asyncio
import os
import re
from collections import deque
from datetime import UTC, datetime

from data.ai_data import PERSONALITIES
from discord.ext import commands
from openai import OpenAI
from utils.discord_helpers import send_smart_message

# Import your existing utilities
from utils.logger import bot_log


class AICoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1",)
        self.personality = PERSONALITIES.get("Discord")
        self.shared_history = deque(maxlen=10)
        self.history_lock = asyncio.Lock()

    def _format_history_entry(self, username, id, content, timestamp):
        clean_content = re.sub(r"\s+", " ", (content or "").strip())
        time_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{time_text}] {username}({id}): {clean_content}"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user in message.mentions:
            prompt = message.clean_content
            user_entry = self._format_history_entry(message.author.display_name, message.author.id, prompt, message.created_at)

            async with self.history_lock:
                self.shared_history.append(user_entry)
                history_text = "\n".join(self.shared_history)

            user_content = [{"type": "text", "text": f"Shared conversation history (last 10 messages):\n{history_text}"}]

            # Check for images and add them to content
            has_images = False
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    user_content.append({"type": "image_url", "image_url": {"url": attachment.url}})
                    has_images = True

            # Choose model based on whether there are images
            if has_images:
                model = "qwen/qwen3.8-27b"
            else:
                model = "qwen/qwen3.8-27b"

            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self.personality},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=500,
                    temperature=1.2,
                )
                ai_reply = response.choices[0].message.content
                ai_entry = self._format_history_entry(self.bot.user.display_name, self.bot.user.id, ai_reply, datetime.now(UTC))
                async with self.history_lock:
                    self.shared_history.append(ai_entry)

                await send_smart_message(message, ai_reply, is_reply=True)
                return ai_reply
            except Exception as e:
                bot_log(f"AI response error: {e}", level="error", important=True)
                await send_smart_message(message, "Sorry, I encountered an error while processing your request.")
def setup(bot):
    bot.add_cog(AICoreCog(bot))
