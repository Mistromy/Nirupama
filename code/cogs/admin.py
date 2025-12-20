import discord
from discord.ext import commands
from discord.commands import Option
import sys
import os
from discord.ui import InputText
import subprocess
from utils.git_format import format_git_output


# 1. IMPORTS (Dependencies)
from utils.logger import bot_log


# ==================== ADDING NEW COMMANDS ====================
# This admin panel is designed for easy extensibility!
# 
# TO ADD A NEW COMMAND:
# 1. Create a new View class (or Modal class if needed)
#    - View example: class MyCommandView(discord.ui.View)
#    - Modal example: class MyCommandModal(discord.ui.Modal)
# 
# 2. Add a button method in AdminMainView:
#    @discord.ui.button(label="My Command", style=discord.ButtonStyle.blurple)
#    async def my_command_button(self, button, interaction):
#        view = MyCommandView(self.bot, self.cog)
#        await interaction.response.edit_message(content="...", view=view)
# 
# 3. That's it! The button will appear in the main panel automatically
# 
# EXAMPLE: Adding a command that sets prefix:
#    - Create SetPrefixModal with a text input
#    - Add the button method pointing to it
#    - Done!
# ============================================================


# ==================== STATUS VIEW ====================

class StatusDropdowns(discord.ui.View):
    """View for status configuration with 2 dropdowns and text input button"""
    def __init__(self, bot, cog):
        super().__init__(timeout=300)
        self.bot = bot
        self.cog = cog
        self.selected_status = None
        self.selected_activity_type = None
        
        # Status dropdown
        status_options = [
            discord.SelectOption(label=k, value=k)
            for k in cog.status_map.keys()
        ]
        self.add_item(StatusSelect(status_options, self))
        
        # Activity type dropdown
        activity_options = [
            discord.SelectOption(label=k, value=k)
            for k in cog.activity_map.keys()
        ]
        self.add_item(ActivityTypeSelect(activity_options, self))

    @discord.ui.button(label="Set Activity Name", style=discord.ButtonStyle.blurple)
    async def activity_name_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.selected_status or not self.selected_activity_type:
            await interaction.response.send_message("❌ Please select status and activity type first!", ephemeral=True)
            return
        
        modal = ActivityNameModal(self.bot, self.cog, self.selected_status, self.selected_activity_type)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("**🎛️ Admin Control Panel**", view=AdminMainView(self.bot, self.cog), ephemeral=True)


class StatusSelect(discord.ui.Select):
    """Dropdown for selecting bot status"""
    def __init__(self, options, parent_view):
        self.parent_view = parent_view
        super().__init__(
            placeholder="Select status...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_status = self.values[0]
        await interaction.response.defer()


class ActivityTypeSelect(discord.ui.Select):
    """Dropdown for selecting activity type"""
    def __init__(self, options, parent_view):
        self.parent_view = parent_view
        super().__init__(
            placeholder="Select activity type...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_activity_type = self.values[0]
        await interaction.response.defer()


class ActivityNameModal(discord.ui.Modal):
    """Modal for custom activity name"""
    def __init__(self, bot, cog, status: str, activity_type: str):
        super().__init__(title="Set Activity Name")
        self.bot = bot
        self.cog = cog
        self.status = status
        self.activity_type = activity_type

        # Using InputText instead of TextInput
        self.activity_name = InputText(
            label="Activity Name",
            placeholder="e.g., /help or your game name",
            required=True,
            max_length=100
        )
        self.add_item(self.activity_name)

    async def on_submit(self, interaction: discord.Interaction):
        chosenstatus = self.cog.status_map.get(self.status, discord.Status.online)
        chosenactivitytype = self.cog.activity_map.get(self.activity_type, discord.ActivityType.playing)
        activity_name_value = self.activity_name.value

        activity = discord.Activity(type=chosenactivitytype, name=activity_name_value)
        await self.bot.change_presence(status=chosenstatus, activity=activity)
        bot_log(f"Status updated by {interaction.user.name} to {self.status} with activity '{activity_name_value}'", level="info")
        await interaction.response.send_message(
            f"✅ Status updated to `{self.status}` ({self.activity_type}: `{activity_name_value}`)",
            ephemeral=True
        )


# ==================== VIEWS/DROPDOWNS ====================

class CogSelectDropdown(discord.ui.Select):
    """Dropdown for selecting which cog to manage"""
    def __init__(self, bot, action: str, cog):
        self.bot = bot
        self.action = action
        self.cog = cog
        
        options = [
            discord.SelectOption(label=ext_name, description=ext_name)
            for ext_name in list(bot.extensions.keys())[:25]  # Discord limit of 25 options
        ]
        
        super().__init__(
            placeholder=f"Select a cog to {action}...",
            min_values=1,
            max_values=1,
            options=options if options else [discord.SelectOption(label="No cogs loaded", value="none")]
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No cogs available", ephemeral=True)
            return

        cog_name = self.values[0]
        try:
            if self.action == "reload":
                self.bot.reload_extension(cog_name)
                await interaction.response.send_message(f"✅ Reloaded cog: `{cog_name}`", ephemeral=True)
                bot_log(f"{cog_name} reloaded by {interaction.user.name}", level="info")
            elif self.action == "unload":
                self.bot.unload_extension(cog_name)
                await interaction.response.send_message(f"✅ Unloaded cog: `{cog_name}`", ephemeral=True)
                bot_log(f"{cog_name} unloaded by {interaction.user.name}", level="info")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to {self.action} cog `{cog_name}`: {e}", ephemeral=True)
            bot_log(f"Failed to {self.action} cog {cog_name}: {e}", level="error")


class CogManagementView(discord.ui.View):
    """View for cog management with dropdown"""
    def __init__(self, bot, action: str, cog):
        super().__init__(timeout=300)
        self.bot = bot
        self.action = action
        self.cog = cog
        self.add_item(CogSelectDropdown(bot, action, cog))

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("**🎛️ Admin Control Panel**", view=AdminMainView(self.bot, self.cog), ephemeral=True)


class ServersListView(discord.ui.View):
    """View for displaying servers list"""
    def __init__(self, bot, cog):
        super().__init__(timeout=300)
        self.bot = bot
        self.cog = cog

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("**🎛️ Admin Control Panel**", view=AdminMainView(self.bot, self.cog), ephemeral=True)


class AdminMainView(discord.ui.View):
    """Main admin panel view with all command buttons"""
    def __init__(self, bot, cog):
        super().__init__(timeout=300)
        self.bot = bot
        self.cog = cog

    @discord.ui.button(label="Reload Cog", style=discord.ButtonStyle.blurple)
    async def reload_cog_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = CogManagementView(self.bot, "reload", self.cog)
        await interaction.response.send_message(content="**Select a cog to reload:**", view=view, ephemeral=True)

    @discord.ui.button(label="Unload Cog", style=discord.ButtonStyle.blurple)
    async def unload_cog_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = CogManagementView(self.bot, "unload", self.cog)
        await interaction.response.send_message(content="**Select a cog to unload:**", view=view, ephemeral=True)

    @discord.ui.button(label="Change Status", style=discord.ButtonStyle.blurple)
    async def status_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = StatusDropdowns(self.bot, self.cog)
        await interaction.response.send_message(content="**Set Bot Status and Activity:**\n1. Select status\n2. Select activity type\n3. Click 'Set Activity Name'", view=view, ephemeral=True)

    @discord.ui.button(label="List Servers", style=discord.ButtonStyle.blurple)
    async def servers_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        serverlisttext = "\n".join([guild.name for guild in self.bot.guilds])
        await interaction.response.send_message(
            content=f"**Servers ({len(self.bot.guilds)}):**\n```\n{serverlisttext}\n```",
            view=ServersListView(self.bot, self.cog),
            ephemeral=True
        )
        bot_log(f"/servers ran by {interaction.user.name}. Returned {len(self.bot.guilds)} guild(s)", level="info")

    @discord.ui.button(label="Git Pull", style=discord.ButtonStyle.green)
    async def git_pull_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        formatted = format_git_output(result.stdout + result.stderr)
        await interaction.response.send_message(
            content=f"**Git Pull Result:**\n```\n{result.stdout}\n```",
            ephemeral=True
        )
        
        bot_log(f"Git pull executed by {interaction.user.name}", level="info")

    @discord.ui.button(label="Wake up", style=discord.ButtonStyle.green)
    async def wake_up_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("🌞 Waking up from invisible...", ephemeral=True)
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="/help"))
        bot_log(f"Bot set to online by {interaction.user.name}", level="info")
        # Optionally reload all cogs
        for ext_name in os.listdir("code/cogs"):
            if ext_name.endswith(".py"):
                cog_name = f"cogs.{ext_name[:-3]}"
                try:
                    if cog_name not in self.bot.extensions:
                        self.bot.load_extension(cog_name)
                except Exception as e:
                    bot_log(f"Failed to load {cog_name}: {e}", level="error")

    # @discord.ui.button(label="Load Cog", style=discord.ButtonStyle.green)

    # @discord.ui.button(label="Load All Cogs", style=discord.ButtonStyle.green)

    @discord.ui.button(label="Fake Offline", style=discord.ButtonStyle.danger)
    async def fake_offline_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("🤫 Going invisible (fake offline)...", ephemeral=True)
        await self.bot.change_presence(status=discord.Status.invisible)
        bot_log(f"Bot set to invisible by {interaction.user.name}", level="info")
        for ext_name in list(self.bot.extensions.keys()):
            if ext_name != "cogs.admin":
                try:
                    self.bot.unload_extension(ext_name)
                except Exception as e:
                    bot_log(f"Failed to unload {ext_name}: {e}", level="error")

    @discord.ui.button(label="Shutdown", style=discord.ButtonStyle.danger)
    async def shutdown_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("🛑 Shutting down...", ephemeral=True)
        bot_log(f"Shutdown initiated by {interaction.user.name}", level="critical")
        self.bot.exit_code = 0
        await self.bot.close()

    @discord.ui.button(label="Reboot", style=discord.ButtonStyle.danger)
    async def reboot_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 Rebooting system...", ephemeral=True)
        bot_log(f"Reboot initiated by {interaction.user.name}", level="warning")
        self.bot.exit_code = 2
        await self.bot.close()
        
class admincommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Status and activity maps
    status_map = {
        "Online": discord.Status.online,
        "Idle": discord.Status.idle,
        "Do Not Disturb": discord.Status.dnd,
        "Invisible": discord.Status.invisible
    }
    
    activity_map = {
        "Playing": discord.ActivityType.playing,
        "Streaming": discord.ActivityType.streaming,
        "Listening": discord.ActivityType.listening,
        "Watching": discord.ActivityType.watching,
        "Competing": discord.ActivityType.competing,
        "Custom": discord.ActivityType.custom
    }

    async def admin_check(self, ctx):
        """Check if user is admin"""
        if ctx.author.id != 859371145076932619:
            await ctx.respond("🚫 Thout art not worthy!", ephemeral=True)
            return False
        return True

    @discord.slash_command(description="Opens Developer Options", name="admin")
    async def admin_panel(self, ctx):
        """Main admin panel command"""
        # Check if user is admin
        if not await self.admin_check(ctx):
            return

        bot_log(f"Admin panel accessed by {ctx.author.name}", level="info")
        await ctx.respond("**Dev Options**", view=AdminMainView(self.bot, self), ephemeral=True)


def setup(bot):
    bot.add_cog(admincommands(bot))