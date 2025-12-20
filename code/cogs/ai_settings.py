import discord
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, InputText
from utils.logger import bot_log
from utils.ai_state import ai_state  # Import the shared state
from data.ai_data import PERSONALITIES, TOOLS, THINKING_MODES, MODELS, PRESETS

OWNER_ID = 859371145076932619

class TemperatureModal(Modal):
    def __init__(self, parent_view):
        super().__init__(title="Set Temperature")
        self.parent_view = parent_view
        self.add_item(InputText(
            label="Value (0.0 - 2.0)", 
            placeholder=str(ai_state.temperature),
            value=str(ai_state.temperature)
        ))

    async def callback(self, interaction: discord.Interaction):
        try:
            val = float(self.children[0].value)
            ai_state.temperature = max(0.0, min(2.0, val))
            await self.parent_view.refresh_message(interaction)
            bot_log(f"Temperature set to {ai_state.temperature}", category="Settings")
        except ValueError:
            await interaction.response.send_message("Invalid number.", ephemeral=True)

class SettingsView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.build_ui()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("What do you think you're doing? ", ephemeral=True)
            return False
        return True

    def build_ui(self):
        # 1. Model
        m_opts = [discord.SelectOption(label=k, description=v, default=(v == ai_state.current_model)) 
                  for k, v in MODELS.items()]
        self.model_sel = Select(placeholder="Select Model", options=m_opts, row=0)
        self.model_sel.callback = self.model_cb
        self.add_item(self.model_sel)

        # 2. Personality (Limit 25)
        p_keys = list(PERSONALITIES.keys())[:25]
        p_opts = [discord.SelectOption(label=k, default=(k == ai_state.current_personality_name)) for k in p_keys]
        self.pers_sel = Select(placeholder="Select Personality", options=p_opts, row=1)
        self.pers_sel.callback = self.pers_cb
        self.add_item(self.pers_sel)

        # 3. Thinking
        t_opts = [discord.SelectOption(label=k, value=str(v), default=(v == ai_state.current_thinking_mode)) 
                  for k, v in THINKING_MODES.items()]
        self.think_sel = Select(placeholder="Thinking Budget", options=t_opts, row=2)
        self.think_sel.callback = self.think_cb
        self.add_item(self.think_sel)
        
        # 4. Preset
        pr_opts = [discord.SelectOption(label=k) for k in PRESETS.keys()]
        self.preset_sel = Select(placeholder="Load Preset...", options=pr_opts, row=3)
        self.preset_sel.callback = self.preset_cb
        self.add_item(self.preset_sel)

        # 5. Buttons
        style = discord.ButtonStyle.green if ai_state.debug_mode else discord.ButtonStyle.grey
        self.debug_btn = Button(label=f"Debug: {'ON' if ai_state.debug_mode else 'OFF'}", style=style, row=4)
        self.debug_btn.callback = self.debug_cb
        self.add_item(self.debug_btn)

        self.hist_btn = Button(label=f"History: {ai_state.history_mode.title()}", style=discord.ButtonStyle.blurple, row=4)
        self.hist_btn.callback = self.hist_cb
        self.add_item(self.hist_btn)

        self.temp_btn = Button(label=f"Temp: {ai_state.temperature}", style=discord.ButtonStyle.secondary, row=4)
        self.temp_btn.callback = self.temp_cb
        self.add_item(self.temp_btn)
        
        self.tools_btn = Button(label="Manage Tools", style=discord.ButtonStyle.secondary, row=4)
        self.tools_btn.callback = self.tools_cb
        self.add_item(self.tools_btn)

    async def refresh_message(self, interaction):
        self.clear_items()
        self.build_ui()
        embed = get_settings_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # Callbacks
    async def model_cb(self, interaction):
        selected_label = self.model_sel.values[0]
        ai_state.current_model = MODELS[selected_label]
        await self.refresh_message(interaction)

    async def pers_cb(self, interaction):
        ai_state.current_personality_name = self.pers_sel.values[0]
        await self.refresh_message(interaction)

    async def think_cb(self, interaction):
        ai_state.current_thinking_mode = int(self.think_sel.values[0])
        await self.refresh_message(interaction)
        
    async def preset_cb(self, interaction):
        if ai_state.apply_preset(self.preset_sel.values[0]):
            await self.refresh_message(interaction)

    async def debug_cb(self, interaction):
        ai_state.debug_mode = not ai_state.debug_mode
        await self.refresh_message(interaction)

    async def hist_cb(self, interaction):
        modes = ["off", "separate", "unified"]
        idx = modes.index(ai_state.history_mode)
        ai_state.history_mode = modes[(idx + 1) % len(modes)]
        await self.refresh_message(interaction)

    async def temp_cb(self, interaction):
        await interaction.response.send_modal(TemperatureModal(self))
        
    async def tools_cb(self, interaction):
        await interaction.response.send_message("Select tools:", view=ToolsView(), ephemeral=True)

class ToolsView(View):
    def __init__(self):
        super().__init__(timeout=180)
        options = [
            discord.SelectOption(label=k, description=v[:100], default=(k in ai_state.enabled_tools))
            for k, v in TOOLS.items()
        ]
        self.sel = Select(placeholder="Select active tools...", min_values=0, max_values=len(options), options=options)
        self.sel.callback = self.callback
        self.add_item(self.sel)

    async def interaction_check(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("⛔ Denied.", ephemeral=True)
            return False
        return True

    async def callback(self, interaction):
        ai_state.enabled_tools = self.sel.values
        await interaction.response.edit_message(content=f"✅ Tools: {', '.join(self.sel.values)}", view=None)

def get_settings_embed():
    embed = discord.Embed(title="🧠 AI Control Panel", color=discord.Color.teal())
    
    # Reverse lookup thinking label
    t_label = next((k for k, v in THINKING_MODES.items() if v == ai_state.current_thinking_mode), str(ai_state.current_thinking_mode))
    
    embed.add_field(name="Model", value=f"`{ai_state.current_model}`", inline=True)
    embed.add_field(name="Personality", value=f"`{ai_state.current_personality_name}`", inline=True)
    embed.add_field(name="Thinking", value=f"`{t_label}`", inline=True)
    embed.add_field(name="Temperature", value=f"`{ai_state.temperature}`", inline=True)
    embed.add_field(name="History", value=f"`{ai_state.history_mode}`", inline=True)
    embed.add_field(name="Debug", value=f"{'✅' if ai_state.debug_mode else '❌'}", inline=True)
    
    tools = ", ".join([f"`{t}`" for t in ai_state.enabled_tools]) or "*None*"
    embed.add_field(name="Tools", value=tools, inline=False)
    return embed

class AISettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Open AI Settings")
    async def settings(self, ctx):
        await ctx.respond(embed=get_settings_embed(), view=SettingsView())
        bot_log(f"AI settings opened by {ctx.author.name}", category="Settings")

    @discord.slash_command(description="Manage Tools")
    async def tools(self, ctx):
        await ctx.respond("Tools:", view=ToolsView(), ephemeral=True)
        bot_log(f"Tools management opened by {ctx.author.name}", category="Settings")

def setup(bot):
    bot.add_cog(AISettingsCog(bot))