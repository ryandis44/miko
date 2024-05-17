'''
Settings cog for allowing users to change their Miko settings
'''



import discord
import os

from cogs_cmd.Settings.Views import SettingsView
from Database.MikoCore import MikoCore
from discord import app_commands
from discord.ext import commands

class SettingsCog(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client



    @app_commands.command(name="settings", description=f"{os.getenv('APP_CMD_PREFIX')}Modify Miko settings for yourself or this guild (if you have permission)")
    @app_commands.guild_only
    async def settings(self, interaction: discord.Interaction):

        await SettingsView(original_interaction=interaction).ainit()

    @app_commands.command(name="msettings", description=f"{os.getenv('APP_CMD_PREFIX')}Modify Miko settings for yourself or this guild (if you have permission)")
    @app_commands.guild_only
    async def msettings(self, interaction: discord.Interaction):

        await SettingsView(original_interaction=interaction).ainit()

    async def interaction_check(self, interaction: discord.Interaction):
        mc = MikoCore()
        await interaction.response.send_message(content=mc.tunables('LOADING_EMOJI'), ephemeral=True)
        return True

async def setup(client: commands.Bot):
    await client.add_cog(SettingsCog(client))