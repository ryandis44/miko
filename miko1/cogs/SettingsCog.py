import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from Database.GuildObjects import MikoTextChannel
from cogs_cmd.Settings.Views import SettingsView
from Database.tunables import *
from Database.MySQL import Database
import os
from dotenv import load_dotenv
load_dotenv()

sc = Database("SettingsCog.py")


class SettingsCog(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     self.tree = app_commands.CommandTree(self.client)


    @app_commands.command(name="settings", description=f"{os.getenv('APP_CMD_PREFIX')}Modify Miko settings for yourself or this guild (if you have permission)")
    @app_commands.guild_only
    async def settings(self, interaction: discord.Interaction):

        await SettingsView(original_interaction=interaction).ainit()

    @app_commands.command(name="msettings", description=f"{os.getenv('APP_CMD_PREFIX')}Modify Miko settings for yourself or this guild (if you have permission)")
    @app_commands.guild_only
    async def msettings(self, interaction: discord.Interaction):

        await SettingsView(original_interaction=interaction).ainit()

    async def interaction_check(self, interaction: discord.Interaction):
        
        await MikoTextChannel(
                channel=interaction.channel if interaction.channel.type not in THREAD_TYPES else interaction.channel.parent,
                client=interaction.client
            ).ainit()
        await interaction.response.send_message(content=tunables('LOADING_EMOJI'), ephemeral=True)
        return True

async def setup(client: commands.Bot):
    await client.add_cog(SettingsCog(client))