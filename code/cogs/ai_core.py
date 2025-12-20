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
from utils.ai_state import ai_state
from data.ai_data import THINKING_MODES

# --- 1. THE TOOL PROCESSOR (Kept from your original code) ---
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
            # Create file object
            import io
            files_to_attach.append(discord.File(fp=io.StringIO(content), filename=fname))
            
            replacement = f"*Code attached as {fname}*"
            # If user wants to keep code in chat
            if retention and retention.lower() == "keep":
                lang = fname.split('.')[-1] if '.' in fname else 'python'
                replacement = f"```{lang}\n{content}\n```\n" + replacement
            
            processed_text = processed_text.replace(m.group(0), replacement)
            used_tools.append(f"code:{fname}")

        # {react:emoji}
        for m in re.finditer(r'\{react:([^}]+)\}', processed_text):
            processed_text = processed_text.replace(m.group(0), "")
            used_tools.append(f"react:{m.group(1).strip()}")

        # {tenor:term}
        for m in re.finditer(r'\{tenor:([^}]+)\}', processed_text):
            processed_text = processed_text.replace(m.group(0), f"*[Tenor GIF: {m.group(1).strip()}]*")
            used_tools.append(f"tenor:{m.group(1).strip()}")

        # {aiimage:desc}
        for m in re.finditer(r'\{aiimage:([^}]+)\}', processed_text):
            processed_text = processed_text.replace(m.group(0), f"*[Image Gen: {m.group(1).strip()}]*")
            used_tools.append(f"aiimage:{m.group(1).strip()}")

        # {localimage:file}
        for m in re.finditer(r'\{localimage:([^}]+)\}', processed_text):
            fname = m.group(1).strip()
            if os.path.exists(fname):
                files_to_attach.append(discord.File(fname))
                processed_text = processed_text.replace(m.group(0), f"*Attached: {fname}*")
                used_tools.append(f"localimage:{fname}")
            else:
                processed_text = processed_text.replace(m.group(0), f"*Missing File: {fname}*")

        if "{newmessage}" in processed_text: used_tools.append("newmessage")

        return processed_text, files_to_attach, used_tools

    async def handle_reactions(self, text, message):
        for m in re.finditer(r'\{react:([^}]+)\}', text):
            try: await message.add_reaction(m.group(1).strip())
            except: pass

class AICoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tool_processor = ToolProcessor(bot)

        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user in message.mentions:
            prompt = message.content
            # prompt = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()
            
            start_time = int(time.time())
            waiting = await message.reply("<a:typing:1330966203602305035> <t:" + str(start_time) + ":R>")
            
            try:
                messages = [
                    {"role": "system", "content": ai_state.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            
                loop = asyncio.get_running_loop()
                
                response = await loop.run_in_executor(None, lambda: self.client.chat.completions.create(
                    model=ai_state.current_model,
                    messages=messages,
                    temperature=ai_state.temperature,
                    # These headers help OpenRouter track your app (optional but good)
                    # extra_headers={
                    #     "HTTP-Referer": "https://mistromy.github.io/Nirupama/",
                    #     "X-Title": "Nirupama Discord Bot",
                    # }
                ))

                raw_text = response.choices[0].message.content
                elapsed = int(time.time() - start_time)

                # 3. Process Tools (Split messages, handle code blocks, etc.)
                final_text, files, tools = await self.tool_processor.process_tools(raw_text, message.channel)

                # 4. Debug Append
                if ai_state.debug_mode:
                    debug = (f"**Temp:** `{ai_state.temperature}` | **Model:** `{ai_state.current_model}` | "
                            f"**Time:** `{elapsed}s`")
                    final_text += f"\n\n## Debug Info\n{debug}"

                # 5. Send Message
                await send_smart_message(message, final_text, is_reply=True, files=files)
                
                # 6. Post-Send Actions (Reactions)
                await self.tool_processor.handle_reactions(raw_text, message)
                
                bot_log(f"Replied to {message.author} using {ai_state.current_model}", category="AI")

            except Exception as e:
                bot_log(f"AI Error: {e}", level="error", category="AI")
                await message.reply(f"**Big Oopsie** <a:Rage:923565182800769064>: {e}")
            finally:
                try: await waiting.delete()
                except: pass

def setup(bot):
    bot.add_cog(AICoreCog(bot))