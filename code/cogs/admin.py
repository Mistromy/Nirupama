import discord
from discord.ext import commands
from discord.commands import Option
import sys
import os


# 1. IMPORTS (Dependencies)
# Just like "Add Component" or "Cast To".
# If you need your global variables, import ai_state.
# If you need to log things, import bot_log.
from utils.logger import bot_log
# from utils.ai_state import ai_state  <-- Uncomment if you need shared data

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    async def get_extensions(self, ctx: discord.AutocompleteContext):
        return list(self.bot.extensions.keys())
    
    @discord.slash_command(description="Reload specified cog")
    async def reload_cog(self, ctx, cog_name: str = Option(autocomplete=get_extensions)):
        try:
            self.bot.reload_extension(cog_name)
            await ctx.respond(f"Reloaded cog: {cog_name}", ephemeral=True)
            bot_log(f"{cog_name} reloaded by {ctx.author.name}", level="info")
        except Exception as e:
            await ctx.respond(f"Failed to reload cog: {cog_name}. Error: {e}", ephemeral=True)
            bot_log(f"Failed to reload cog {cog_name} by {ctx.author.name}: {e}", level="error")
        
    @discord.slash_command(description="Unload specified cog")
    async def unload_cog(self, ctx, cog_name: str = Option(autocomplete=get_extensions)):
        try:
            self.bot.unload_extension(cog_name)
            await ctx.respond(f"Unloaded cog: {cog_name}", ephemeral=True)
            bot_log(f"{cog_name} unloaded by {ctx.author.name}", level="info")
        except Exception as e:
            await ctx.respond(f"Failed to unload cog: {cog_name}. Error: {e}", ephemeral=True)
            bot_log(f"Failed to unload cog {cog_name} by {ctx.author.name}: {e}", level="error")

    @discord.slash_command(description="Kills the bot")
    async def kill(self, ctx):
        await ctx.respond("Shutting down...", ephemeral=False)
        bot_log(f"Shutdown initiated by {ctx.author.name}", level="critical")
        self.bot.exit_code = 0
        await self.bot.close()

    @discord.slash_command(description="Reboots the bot")
    async def reboot(self, ctx):
        await ctx.respond("Rebooting system...", ephemeral=False)
        bot_log(f"Reboot initiated by {ctx.author.name}", level="warning")
        self.bot.exit_code = 2
        await self.bot.close()

    @discord.slash_command(description="List servers")
    async def servers(self, ctx):
        serverlisttext = ""
        for guild in self.bot.guilds:
            serverlisttext = serverlisttext + guild.name + "\n"
        await ctx.respond(f"{serverlisttext}")
        bot_log(f"/servers ran by:{ctx.author.name}. Returned {len(self.bot.guilds)} guild(s)", level="info")

    @discord.slash_command(description="Change bot status")
    async def status(self, ctx, status: str):
        try:
            status_mapping = {
                "online": discord.Status.online,
                "idle": discord.Status.idle,
                "dnd": discord.Status.dnd,
                "invisible": discord.Status.invisible
            }
            if status.lower() not in status_mapping:
                await ctx.respond("Invalid status. Choose from: online, idle, dnd, invisible.", ephemeral=True)
                return

            await self.bot.change_presence(status=status_mapping[status.lower()])
            await ctx.respond(f"Status changed to {status}.", ephemeral=True)
            bot_log(f"Status changed to {status} by {ctx.author.name}", level="info")
        except Exception as e:
            await ctx.respond(f"Failed to change status. Error: {e}", ephemeral=True)
            bot_log(f"Failed to change status by {ctx.author.name}: {e}", level="error")

def setup(bot):
    bot.add_cog(admin(bot))