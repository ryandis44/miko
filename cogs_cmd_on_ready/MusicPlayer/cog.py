'''
MusicPlayer

Plays music from the internet
'''



import asyncio  
import discord
import os
import wavelink

from Database.MikoCore import MikoCore
from discord import app_commands
from discord.ext import commands
from typing import cast

class MusicPlayer(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client



    @app_commands.command(name="play", description=f"{os.getenv('APP_CMD_PREFIX')}Play content from the internet in voice chat")
    @app_commands.describe(
        search="Search for something..."
    )
    @app_commands.guild_only
    async def play_song(self, interaction: discord.Interaction, search: str) -> None:
        
        ########################################
        mc = MikoCore()
        await interaction.response.send_message(content=mc.tunables('LOADING_EMOJI'), ephemeral=True)
        msg = await interaction.original_response()
        
        await mc.user_ainit(user=interaction.user, client=self.client)
        if mc.profile.feature_enabled('MUSIC_CHANNEL') == 0:
            await msg.edit(content=mc.tunables('COMMAND_DISABLED_GUILD_MESSAGE'))
            return
        elif mc.profile.feature_enabled('MUSIC_CHANNEL') == 2:
            await msg.edit(content=mc.tunables('COMMAND_DISABLED_MESSAGE'))
            return
        ########################################
        
        
        # Ensure user is in a voice channel
        afk = interaction.guild.afk_channel
        if interaction.user.voice is None or \
            (afk is not None and interaction.user.voice.channel.id == afk.id):
            await msg.edit(content=mc.tunables('MESSAGES_VOICE_CHANNEL_REQUIRED'))
            await asyncio.sleep(mc.tunables('QUICK_EPHEMERAL_DELETE_AFTER'))
            try: await msg.delete() # declutter
            except: pass
            return
        
        
        
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            except Exception as e: print(e)
        
        player.autoplay = wavelink.AutoPlayMode.enabled
        
        
        # Lock player to this channel
        if not hasattr(player, "home"):
            player.home = interaction.channel
        elif player.home != interaction.channel:
            await msg.edit(content=(
                f"Someone has already requested music in {player.home.mention}. Please move to that channel to play music."
            ))
            await asyncio.sleep(mc.tunables('QUICK_EPHEMERAL_DELETE_AFTER'))
            try: await msg.delete() # declutter
            except: pass
        
        
        tracks: wavelink.Search = await wavelink.Playable.search(search)
        
        # TODO



    @app_commands.command(name="stop", description=f"{os.getenv('APP_CMD_PREFIX')}Stop playing and leave voice chat")
    @app_commands.guild_only
    async def disconnect(self, interaction: discord.Interaction) -> None:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            await interaction.response.send_message(content="I'm not in a voice channel!", ephemeral=True)
            return
        
        await player.disconnect()
        
        await interaction.response.send_message(content="Disconnected and queue cleared.", ephemeral=True)
    
    

async def setup(client: commands.Bot):
    await client.add_cog(MusicPlayer(client))