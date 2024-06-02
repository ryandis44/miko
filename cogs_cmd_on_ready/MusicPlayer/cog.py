'''
Miko Music 3.0

Plays music from the internet
'''



import asyncio  
import discord
import mafic
import os

from cogs_cmd_on_ready.MusicPlayer.Backend import MikoPlayer
from cogs_cmd_on_ready.MusicPlayer.UI import MikoMusic
from Database.MikoCore import MikoCore
from discord import app_commands
from discord.ext import commands
from typing import cast

class MusicPlayer(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client



    @app_commands.command(name="play", description=f"{os.getenv('APP_CMD_PREFIX')}Play content from the internet in voice chat")
    @app_commands.guild_only
    async def play_song(self, interaction: discord.Interaction) -> None:
        
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
        
        # Ensure a music channel has been set
        if mc.guild.music_channel is None:
            await msg.edit(
                content=(
                    "Error: To use this feature, a server admin with **`Manage Server`** permission must "
                    f"set a music channel using {mc.tunables('SLASH_COMMAND_SUGGEST_SETTINGS')}."
                )
            )
            return
        
        await MikoMusic(mc=mc, msg=msg).ainit()
        


    @app_commands.command(name="stop", description=f"{os.getenv('APP_CMD_PREFIX')}Stop playing and leave voice chat")
    @app_commands.guild_only
    async def disconnect(self, interaction: discord.Interaction) -> None:
        player: MikoPlayer = (interaction.guild.voice_client)
        if not player:
            await interaction.response.send_message(content="I'm not in a voice channel.", ephemeral=True)
            return
        
        await player.disconnect()
        
        await interaction.response.send_message(content="Disconnected and queue cleared.", ephemeral=True)



    # @app_commands.command(name="skip", description=f"{os.getenv('APP_CMD_PREFIX')}Skip current track")
    # @app_commands.guild_only
    # async def skip_track(self, interaction: discord.Interaction) -> None:
    #     await interaction.response.send_message(content="Skipped track.", ephemeral=False)
    #     player: MikoPlayer = (interaction.guild.voice_client)
    #     await player.skip()



    # @app_commands.command(name="queue", description=f"{os.getenv('APP_CMD_PREFIX')}List current player queue")
    # @app_commands.guild_only
    # async def queue(self, interaction: discord.Interaction) -> None:
    #     player: MikoPlayer = (interaction.guild.voice_client)
    #     await interaction.response.send_message(content=[track.title for track in player.queue], ephemeral=False)
    
    

async def setup(client: commands.Bot):
    await client.add_cog(MusicPlayer(client))