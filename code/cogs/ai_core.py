import discord
from discord.ext import commands
import os
import time
import re
import sqlite3
import asyncio
import io
from google import genai
from google.genai import types

from utils.logger import bot_log
from utils.discord_helpers import send_smart_message
from utils.ai_state import ai_state  # Import the shared state
from data.ai_data import THINKING_MODES # Needed for debug lookups

class ToolProcessor:
    def __init__(self, bot):
        self.bot = bot

    async def process_tools(self, text, channel, files_to_attach=None):
        if files_to_attach is None: files_to_attach = []
        processed_text = text
        used_tools = []

        # {code:filename}
        matches = re.finditer(r'\{code:([^:}]+)(?::([^}]+))?\}(.*?)\{endcode\}', text, re.DOTALL)
        for m in matches:
            fname, retention, content = m.group(1).strip(), m.group(2), m.group(3).strip()
            files_to_attach.append(discord.File(fp=io.StringIO(content), filename=fname))
            
            replacement = f"*Code attached as {fname}*"
            if retention and retention.lower() == "keep":
                lang = fname.split('.')[-1] if '.' in fname else 'python'
                replacement = f"```{lang}\n{content}\n```\n" + replacement
            
            processed_text = processed_text.replace(m.group(0), replacement)
            used_tools.append(f"code:{fname}")

        # {react:emoji}
        for m in re.finditer(r'\{react:([^}]+)\}', processed_text):
            emoji = m.group(1).strip()
            processed_text = processed_text.replace(m.group(0), "")
            used_tools.append(f"react:{emoji}")

        # {tenor:term}
        for m in re.finditer(r'\{tenor:([^}]+)\}', processed_text):
            processed_text = processed_text.replace(m.group(0), f"*[Tenor: {m.group(1).strip()}]*")
            used_tools.append(f"tenor:{m.group(1).strip()}")

        # {aiimage:desc}
        for m in re.finditer(r'\{aiimage:([^}]+)\}', processed_text):
            processed_text = processed_text.replace(m.group(0), f"*[Image: {m.group(1).strip()}]*")
            used_tools.append(f"aiimage:{m.group(1).strip()}")

        # {localimage:file}
        for m in re.finditer(r'\{localimage:([^}]+)\}', processed_text):
            fname = m.group(1).strip()
            if os.path.exists(fname):
                files_to_attach.append(discord.File(fname))
                processed_text = processed_text.replace(m.group(0), f"*Attached: {fname}*")
                used_tools.append(f"localimage:{fname}")
            else:
                processed_text = processed_text.replace(m.group(0), f"*Missing: {fname}*")

        if "{newmessage}" in processed_text: used_tools.append("newmessage")

        return processed_text, files_to_attach, used_tools

    async def handle_reactions(self, text, message):
        for m in re.finditer(r'\{react:([^}]+)\}', text):
            try: await message.add_reaction(m.group(1).strip())
            except: pass

class AICoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.tool_processor = ToolProcessor(bot)
        self.init_history_db()

    def init_history_db(self):
        conn = sqlite3.connect('conversation_history.db')
        conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, user_id TEXT, username TEXT, timestamp INTEGER, message TEXT, is_bot BOOLEAN)")
        conn.commit()
        conn.close()

    def add_history(self, uid, uname, msg, is_bot=False):
        if ai_state.history_mode == "off": return
        conn = sqlite3.connect('conversation_history.db')
        conn.execute("INSERT INTO history (user_id, username, timestamp, message, is_bot) VALUES (?, ?, ?, ?, ?)",
                     (uid, uname, int(time.time()), msg, is_bot))
        conn.commit()
        conn.close()

    def get_context(self, uid):
        if ai_state.history_mode == "off": return ""
        conn = sqlite3.connect('conversation_history.db')
        # Simple Logic: Get last 10 messages total
        rows = conn.execute("SELECT username, message, is_bot FROM history ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        
        ctx = []
        for r in reversed(rows):
            name = "Bot" if r[2] else r[0]
            ctx.append(f"{name}: {r[1][:200]}")
        return "\n\nRecent Conversation:\n" + "\n".join(ctx) if ctx else ""

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or self.bot.user not in message.mentions:
            return

        start_time = time.time()
        waiting = await message.reply("<a:typing:1330966203602305035> Thinking...")
        
        try:
            # 1. Prepare Input
            self.add_history(str(message.author.id), message.author.display_name, message.content)
            prompt_parts = [message.content]
            
            # Attachments
            if message.attachments:
                for att in message.attachments:
                    if att.content_type and att.content_type.startswith('image'):
                        prompt_parts.append(types.Part.from_bytes(data=await att.read(), mime_type=att.content_type))
                    elif att.filename.endswith(('.py', '.txt', '.json', '.md')):
                        text = await att.read()
                        prompt_parts.append(f"\n\nFile {att.filename}:\n{text.decode('utf-8', errors='ignore')}\n")

            # History
            hist = self.get_context(str(message.author.id))
            if hist: prompt_parts.append(hist)

            # 2. Call AI
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: self.client.models.generate_content(
                model=ai_state.current_model,
                config=types.GenerateContentConfig(
                    temperature=ai_state.temperature,
                    thinking_config=types.ThinkingConfig(thinking_budget=ai_state.current_thinking_mode),
                    system_instruction=ai_state.system_prompt, # READS DYNAMIC PROMPT
                ),
                contents=prompt_parts
            ))

            raw_text = response.candidates[0].content.parts[0].text
            elapsed = int(time.time() - start_time)

            # 3. Process
            final_text, files, tools = await self.tool_processor.process_tools(raw_text, message.channel)

            if ai_state.debug_mode:
                t_label = next((k for k, v in THINKING_MODES.items() if v == ai_state.current_thinking_mode), str(ai_state.current_thinking_mode))
                debug = (f"**Temp:** `{ai_state.temperature}` | **Model:** `{ai_state.current_model}` | "
                         f"**Mode:** `{t_label}` | **Time:** `{elapsed}s`")
                final_text += f"\n\n## Debug Info\n{debug}"

            # 4. Send
            await send_smart_message(message, final_text, is_reply=True, files=files)
            await self.tool_processor.handle_reactions(raw_text, message)
            
            self.add_history(str(self.bot.user.id), "Bot", final_text, is_bot=True)
            bot_log(f"Replied to {message.author}", category="AI")

        except Exception as e:
            bot_log(f"AI Error: {e}", level="error", category="AI")
            await message.reply(f"❌ Error: {e}")
        finally:
            try: await waiting.delete()
            except: pass

def setup(bot):
    bot.add_cog(AICoreCog(bot))