# Per guild command
# @bot.slash_command(
#     description="Reboots the bot.",
#     guild_ids=[YOUR_GUILD_ID],  # Only appears in your guild
#     default_member_permissions=discord.Permissions(administrator=True)
# )
# async def reboot(ctx):
#     # ...existing code...

# Only admin command
#     @bot.slash_command(
#     description="Reboots the bot.",
#     default_member_permissions=discord.Permissions(administrator=True),
#     guild_only=True
# )
# async def reboot(ctx):
#     # ...existing code...