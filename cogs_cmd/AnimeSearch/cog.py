'''
AnimeSearch

Allows users to type the name of an anime and pull details about
it from AniList API
'''



import discord
import os

from cogs_cmd.AnimeSearch.AnimeSearch import AnimeSearchView
from Database.MikoCore import MikoCore
from discord import app_commands
from discord.ext import commands

class AnimeSearch(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client



    @app_commands.command(name="animesearch", description=f"{os.getenv('APP_CMD_PREFIX')}Search for an anime and view details about it (source: AniList)")
    @app_commands.describe(
        anime="Name of the anime you want to search for"
    )
    async def animesearch(self, interaction: discord.Interaction, anime: str):

        # await SettingsView(original_interaction=interaction).ainit()
        await AnimeSearchView(original_interaction=interaction, search=anime).ainit()



    @app_commands.command(name="as", description=f"{os.getenv('APP_CMD_PREFIX')}Search for an anime and view details about it (source: AniList)")
    @app_commands.describe(
        anime="Name of the anime you want to search for"
    )
    async def asearch(self, interaction: discord.Interaction, anime: str):

        await AnimeSearchView(original_interaction=interaction, search=anime).ainit()



    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.client)
        if mc.profile.cmd_enabled('ANIME_SEARCH') == 0:
            await interaction.response.send_message(content=mc.tunables('COMMAND_DISABLED_GUILD_MESSAGE'), ephemeral=True)
            return False
        elif mc.profile.cmd_enabled('ANIME_SEARCH') == 2:
            await interaction.response.send_message(content=mc.tunables('COMMAND_DISABLED_MESSAGE'), ephemeral=True)
            return False

        await interaction.response.send_message(content=f"{mc.tunables('LOADING_EMOJI')}", ephemeral=False, silent=True)
        return True

async def setup(client: commands.Bot):
    await client.add_cog(AnimeSearch(client))