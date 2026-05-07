import discord
from discord.ext import commands
import asyncio
from utils.logger import bot_log


class MyNewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        bot_log("MyNewCog is ready!", level="info")

        # 1. THE GHOST FIX: Force disconnect any lingering voice states on startup
        for vc in self.bot.voice_clients:
            bot_log(f"Clearing ghost connection in {vc.guild.name}...", level="warning")
            await vc.disconnect(force=True)

    @discord.slash_command(description="Make the AI join your voice channel")
    async def joinvc(self, ctx):
        # Defers the 3-second Discord interaction limit
        await ctx.defer()

        if not ctx.author.voice:
            return await ctx.respond("You need to be in a voice channel first!")

        channel = ctx.author.voice.channel

        # If the bot is already in a VC in this server, kill the old connection first
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)

        try:
            bot_log(f"Attempting DAVE connection to {channel.name}...", level="info")
            # 2. THE TIMEOUT FIX: Lower the timeout so it doesn't hang for 30s if it fails
            await channel.connect(timeout=10.0, reconnect=False)

            await ctx.respond(f"Joined {channel.name} and secured E2EE connection!")

        except asyncio.TimeoutError:
            await ctx.respond("Connection timed out. The DAVE handshake failed.")
        except Exception as e:
            bot_log(f"Voice Error: {e}", level="error")
            await ctx.respond("Failed to join due to an encryption or network error.")


def setup(bot):
    bot.add_cog(MyNewCog(bot))
