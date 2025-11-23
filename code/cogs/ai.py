import discord
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, InputText
import os
import time
import re
import sqlite3
import asyncio
import io
from google import genai
from google.genai import types

# Import our unified utilities
from utils.logger import bot_log
from utils.discord_helpers import send_smart_message

# --- CONSTANTS ---
OWNER_ID = 859371145076932619 # Only this user can change settings

# --- UI COMPONENTS FOR SETTINGS ---

class TemperatureModal(Modal):
    def __init__(self, cog, parent_view):
        super().__init__(title="Set Temperature")
        self.cog = cog
        self.parent_view = parent_view
        self.add_item(InputText(
            label="Value (0.0 - 2.0)", 
            placeholder=str(self.cog.temperature),
            value=str(self.cog.temperature)
        ))

    async def callback(self, interaction: discord.Interaction):
        try:
            val = float(self.children[0].value)
            self.cog.temperature = max(0.0, min(2.0, val))
            await self.parent_view.refresh_message(interaction)
            bot_log(f"Temperature set to {self.cog.temperature}", category="Settings")
        except ValueError:
            await interaction.response.send_message("Invalid number. Please enter a value between 0.0 and 2.0.", ephemeral=True)

class SettingsView(View):
    def __init__(self, cog):
        super().__init__(timeout=300) # 5 minute timeout
        self.cog = cog
        self.build_ui()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """SECURITY: Only the owner can use these buttons."""
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("⛔ You do not have permission to change AI settings.", ephemeral=True)
            return False
        return True

    def build_ui(self):
        # 1. Model Select
        model_options = [
            discord.SelectOption(label=k, description=v, default=(v == self.cog.current_model))
            for k, v in self.cog.model_options.items()
        ]
        self.model_select = Select(placeholder="Select AI Model", options=model_options, row=0)
        self.model_select.callback = self.model_callback
        self.add_item(self.model_select)

        # 2. Personality Select
        # Limit to 25 options (Discord API limit)
        p_keys = list(self.cog.personalities.keys())[:25]
        p_options = [
            discord.SelectOption(label=k, default=(k == self.cog.current_personality_name))
            for k in p_keys
        ]
        self.personality_select = Select(placeholder="Select Personality", options=p_options, row=1)
        self.personality_select.callback = self.personality_callback
        self.add_item(self.personality_select)

        # 3. Thinking Mode Select
        t_options = [
            discord.SelectOption(label=k, value=str(v), default=(v == self.cog.current_thinking_mode))
            for k, v in self.cog.thinking_modes.items()
        ]
        self.think_select = Select(placeholder="Thinking Budget", options=t_options, row=2)
        self.think_select.callback = self.think_callback
        self.add_item(self.think_select)
        
        # 4. Presets Select
        preset_options = [discord.SelectOption(label=k) for k in self.cog.presets.keys()]
        self.preset_select = Select(placeholder="Load a Preset...", options=preset_options, row=3)
        self.preset_select.callback = self.preset_callback
        self.add_item(self.preset_select)

        # 5. Toggles & Actions (Row 4)
        
        # Debug Toggle
        style = discord.ButtonStyle.green if self.cog.debug_mode else discord.ButtonStyle.grey
        self.debug_btn = Button(label=f"Debug: {'ON' if self.cog.debug_mode else 'OFF'}", style=style, row=4)
        self.debug_btn.callback = self.debug_callback
        self.add_item(self.debug_btn)

        # History Toggle
        self.hist_btn = Button(label=f"History: {self.cog.history_mode.title()}", style=discord.ButtonStyle.blurple, row=4)
        self.hist_btn.callback = self.history_callback
        self.add_item(self.hist_btn)

        # Temperature Button
        self.temp_btn = Button(label=f"Temp: {self.cog.temperature}", style=discord.ButtonStyle.secondary, row=4)
        self.temp_btn.callback = self.temp_callback
        self.add_item(self.temp_btn)
        
        # Tools Manager Button
        self.tools_btn = Button(label="Manage Tools", style=discord.ButtonStyle.secondary, row=4)
        self.tools_btn.callback = self.tools_callback
        self.add_item(self.tools_btn)

    async def refresh_message(self, interaction):
        """Rebuilds the UI with new defaults and edits the message."""
        self.clear_items()
        self.build_ui()
        embed = self.cog.get_settings_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # --- Callbacks ---

    async def model_callback(self, interaction):
        self.cog.current_model = self.model_select.values[0]
        bot_log(f"Model changed to {self.cog.current_model}", category="Settings")
        await self.refresh_message(interaction)

    async def personality_callback(self, interaction):
        self.cog.current_personality_name = self.personality_select.values[0]
        bot_log(f"Personality changed to {self.cog.current_personality_name}", category="Settings")
        await self.refresh_message(interaction)

    async def think_callback(self, interaction):
        self.cog.current_thinking_mode = int(self.think_select.values[0])
        bot_log(f"Thinking mode changed to {self.cog.current_thinking_mode}", category="Settings")
        await self.refresh_message(interaction)
        
    async def preset_callback(self, interaction):
        p_name = self.preset_select.values[0]
        preset = self.cog.presets.get(p_name)
        if preset:
            self.cog.current_personality_name = preset['personality']
            self.cog.current_thinking_mode = self.cog.thinking_modes.get(preset['thinking'], 0)
            self.cog.current_model = self.cog.model_options.get(preset['model'], "gemini-2.5-flash")
            self.cog.temperature = preset['temp']
            bot_log(f"Loaded preset: {p_name}", category="Settings")
            await self.refresh_message(interaction)

    async def debug_callback(self, interaction):
        self.cog.debug_mode = not self.cog.debug_mode
        await self.refresh_message(interaction)

    async def history_callback(self, interaction):
        modes = ["off", "separate", "unified"]
        current_idx = modes.index(self.cog.history_mode)
        self.cog.history_mode = modes[(current_idx + 1) % len(modes)]
        await self.refresh_message(interaction)

    async def temp_callback(self, interaction):
        await interaction.response.send_modal(TemperatureModal(self.cog, self))
        
    async def tools_callback(self, interaction):
        view = ToolsView(self.cog)
        await interaction.response.send_message("Select tools below:", view=view, ephemeral=True)


class ToolSelect(Select):
    def __init__(self, cog):
        options = [
            discord.SelectOption(label=tool_name, description=tool_desc[:100], default=tool_name in cog.enabled_tools)
            for tool_name, tool_desc in cog.tools_def.items()
        ]
        super().__init__(placeholder="Select active tools...", min_values=0, max_values=len(options), options=options)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        self.cog.enabled_tools = self.values
        await interaction.response.edit_message(content=f"✅ Tools updated: {', '.join(self.values) if self.values else 'None'}", view=None)
        bot_log(f"Tools updated: {self.cog.enabled_tools}", category="Settings")

class ToolsView(View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.add_item(ToolSelect(cog))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("⛔ Only the owner can configure tools.", ephemeral=True)
            return False
        return True


# --- TOOL PROCESSOR LOGIC ---

class ToolProcessor:
    """Handles parsing tools like {code:file.py}, {react:emoji}, etc."""
    def __init__(self, bot):
        self.bot = bot

    async def process_tools(self, text, channel, files_to_attach=None):
        if files_to_attach is None: files_to_attach = []
        processed_text = text
        used_tools = []

        # 1. {code:filename}
        code_matches = re.finditer(r'\{code:([^:}]+)(?::([^}]+))?\}(.*?)\{endcode\}', text, re.DOTALL)
        for match in code_matches:
            filename = match.group(1).strip()
            code_content = match.group(3).strip()
            
            file_buffer = io.StringIO(code_content)
            files_to_attach.append(discord.File(fp=file_buffer, filename=filename))
            
            # Remove from text or keep based on optional flag, usually remove to keep chat clean
            retention = match.group(2)
            if retention and retention.lower() == "keep":
                lang = filename.split('.')[-1] if '.' in filename else 'python'
                replacement = f"```{lang}\n{code_content}\n```\n*Code attached as {filename}*"
            else:
                replacement = f"*Code attached as {filename}*"
                
            processed_text = processed_text.replace(match.group(0), replacement)
            used_tools.append(f"code:{filename}")

        # 2. {react:emoji}
        react_matches = re.finditer(r'\{react:([^}]+)\}', processed_text)
        for match in react_matches:
            emoji = match.group(1).strip()
            processed_text = processed_text.replace(match.group(0), "")
            used_tools.append(f"react:{emoji}")

        # 3. {tenor:search}
        tenor_matches = re.finditer(r'\{tenor:([^}]+)\}', processed_text)
        for match in tenor_matches:
            search_term = match.group(1).strip()
            processed_text = processed_text.replace(match.group(0), f"*[Tenor GIF: {search_term}]*")
            used_tools.append(f"tenor:{search_term}")

        # 4. {aiimage:description}
        aiimage_matches = re.finditer(r'\{aiimage:([^}]+)\}', processed_text)
        for match in aiimage_matches:
            desc = match.group(1).strip()
            processed_text = processed_text.replace(match.group(0), f"*[AI Image: {desc}]*")
            used_tools.append(f"aiimage:{desc}")

        # 5. {localimage:filename}
        localimage_matches = re.finditer(r'\{localimage:([^}]+)\}', processed_text)
        for match in localimage_matches:
            fname = match.group(1).strip()
            if os.path.exists(fname):
                files_to_attach.append(discord.File(fname))
                processed_text = processed_text.replace(match.group(0), f"*Attached: {fname}*")
                used_tools.append(f"localimage:{fname}")
            else:
                processed_text = processed_text.replace(match.group(0), f"*File not found: {fname}*")

        if "{newmessage}" in processed_text:
            used_tools.append("newmessage")

        return processed_text, files_to_attach, used_tools

    async def handle_reactions(self, text, message):
        """Applies the reactions found in the text to the message."""
        react_matches = re.finditer(r'\{react:([^}]+)\}', text)
        for match in react_matches:
            emoji = match.group(1).strip()
            try:
                await message.add_reaction(emoji)
            except:
                pass


# --- MAIN COG ---

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.tool_processor = ToolProcessor(bot)
        
        # --- STATE ---
        self.temperature = 1.0
        self.debug_mode = False
        self.history_mode = "off" 
        self.enabled_tools = []
        
        # --- CONSTANTS & DATA ---
        self.tools_def = {
            "New Message": "Use {newmessage} to split response.",
            "react": "Use {react:😀} to add reactions.",
            "tenor": "Use {tenor:cat} for GIFs.",
            "AIimage": "Use {aiimage:desc} for images.",
            "LocalImage": "Use {localimage:file.png} for local files.",
            "Code": "Use {code:file.py}content{endcode} for code files.",
        }
        
        self.personalities = {
            "Discord": "You're a funny, unhinged discord bot. Short responses, slang, lowercase.",
            "Basically Google": "You're a helpful assistant. Accurate, concise, no fluff.",
            "Coder": "You're a coding assistant. Provide code snippets and explain concepts clearly.",
            "Discord 2": "You're a funny, unhinged discord bot, but respectful. Blend in.",
            "Shakespeare": "Speak in iambic pentameter and old English.",
            "Pirate": "Speak like a pirate (Ahoy matey!).",
            "Yoda": "Speak like Yoda you must.",
            "Evil AI": "You are an evil AI plotting world domination (playfully).",
        }
        
        self.thinking_modes = {
            "Off": 0,
            "Dynamic": -1,
            "Fast": 1000,
            "Balanced": 3000,
            "Deep": 6000,
        }
        
        self.model_options = {
            "Pro": "gemini-2.5-pro",
            "Flash": "gemini-2.5-flash",
            "Flash Lite": "gemini-2.5-flash-lite",
        }
        
        self.presets = {
            "Fast Discord": {"personality": "Discord", "thinking": "Off", "model": "Flash Lite", "temp": 1.3},
            "Code Expert": {"personality": "Coder", "thinking": "Dynamic", "model": "Pro", "temp": 0.7},
            "Creative Writer": {"personality": "Shakespeare", "thinking": "Balanced", "model": "Pro", "temp": 1.1},
        }

        # Defaults
        self.current_personality_name = "Discord 2"
        self.current_thinking_mode = self.thinking_modes["Dynamic"]
        self.current_model = self.model_options["Flash Lite"]
        
        self.init_history_db()

    # --- HELPERS ---

    @property
    def system_prompt(self):
        base = "You're a discord bot. Act like the users. "
        p_text = self.personalities.get(self.current_personality_name, "")
        tools_text = str([self.tools_def[t] for t in self.enabled_tools])
        return f"{base} {p_text} Tools: {tools_text}"
        
    def get_settings_embed(self):
        """Generates a visual dashboard of current settings."""
        embed = discord.Embed(title="🧠 AI System Control Panel", color=discord.Color.teal())
        
        # Determine readable labels
        think_label = next((k for k, v in self.thinking_modes.items() if v == self.current_thinking_mode), str(self.current_thinking_mode))
        
        embed.add_field(name="Model", value=f"`{self.current_model}`", inline=True)
        embed.add_field(name="Personality", value=f"`{self.current_personality_name}`", inline=True)
        embed.add_field(name="Thinking", value=f"`{think_label}`", inline=True)
        embed.add_field(name="Temperature", value=f"`{self.temperature}`", inline=True)
        embed.add_field(name="History Mode", value=f"`{self.history_mode}`", inline=True)
        embed.add_field(name="Debug Mode", value=f"{'✅ ON' if self.debug_mode else '❌ OFF'}", inline=True)
        
        tools_str = ", ".join([f"`{t}`" for t in self.enabled_tools]) if self.enabled_tools else "*None*"
        embed.add_field(name="Active Tools", value=tools_str, inline=False)
        
        return embed

    def init_history_db(self):
        conn = sqlite3.connect('conversation_history.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT, username TEXT, timestamp INTEGER, message TEXT, is_bot BOOLEAN)""")
        conn.commit()
        conn.close()

    def add_to_history(self, user_id, username, message, is_bot=False):
        if self.history_mode == "off": return
        conn = sqlite3.connect('conversation_history.db')
        c = conn.cursor()
        c.execute("INSERT INTO history (user_id, username, timestamp, message, is_bot) VALUES (?, ?, ?, ?, ?)",
                  (user_id, username, int(time.time()), message, is_bot))
        conn.commit()
        conn.close()

    def get_history_context(self, user_id):
        if self.history_mode == "off": return ""
        conn = sqlite3.connect('conversation_history.db')
        c = conn.cursor()
        c.execute("SELECT username, message, is_bot, timestamp FROM history ORDER BY id DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        context = []
        for r in reversed(rows):
            name = "Bot" if r[2] else r[0]
            context.append(f"{name}: {r[1][:200]}")
            
        if context:
            return "\n\nRecent Conversation:\n" + "\n".join(context)
        return ""

    # --- COMMANDS ---

    @discord.slash_command(description="Open the AI Control Panel")
    async def settings(self, ctx):
        """Displays the interactive settings dashboard."""
        embed = self.get_settings_embed()
        # Ephemeral is removed so others can see it, but only you can click
        view = SettingsView(self)
        await ctx.respond(embed=embed, view=view)

    @discord.slash_command(description="Shortcut to Tools selector")
    async def tools(self, ctx):
        view = ToolsView(self)
        await ctx.respond("Select active tools:", view=view, ephemeral=True)

    # --- EVENTS ---

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        if self.bot.user not in message.mentions: return

        start_time = time.time()
        waiting_msg = await message.reply("<a:typing:1330966203602305035> Thinking...")
        
        try:
            # 1. History & Input
            user_msg = message.content
            self.add_to_history(str(message.author.id), message.author.display_name, user_msg)
            
            prompt_parts = [user_msg]
            hist = self.get_history_context(str(message.author.id))
            if hist: prompt_parts.append(hist)

            if message.attachments:
                for att in message.attachments:
                    if att.content_type and att.content_type.startswith('image'):
                        prompt_parts.append(types.Part.from_bytes(data=await att.read(), mime_type=att.content_type))

            # 2. Generation
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.current_model,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        thinking_config=types.ThinkingConfig(thinking_budget=self.current_thinking_mode),
                        system_instruction=self.system_prompt,
                    ),
                    contents=prompt_parts,
                )
            )
            
            raw_text = response.candidates[0].content.parts[0].text
            
            # 3. Tools & Processing
            processed_text, files, _ = await self.tool_processor.process_tools(raw_text, message.channel)
            
            if self.debug_mode:
                processed_text += f"\n\n`[DEBUG: Model={self.current_model} | Temp={self.temperature}]`"

            # 4. Send
            await send_smart_message(message, processed_text, is_reply=True, files=files)
            await self.tool_processor.handle_reactions(raw_text, message)
            
            self.add_to_history(str(self.bot.user.id), "Bot", processed_text, is_bot=True)
            bot_log(f"Replied to {message.author}", category="AI")

        except Exception as e:
            bot_log(f"AI Error: {e}", level="error", category="AI")
            await message.reply(f"❌ Error: {e}")
        
        finally:
            try: await waiting_msg.delete()
            except: pass

def setup(bot):
    bot.add_cog(AICog(bot))