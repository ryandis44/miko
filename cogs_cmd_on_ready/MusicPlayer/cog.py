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
        
        player: MikoPlayer = (interaction.guild.voice_client)
        if not player:
            await msg.edit(content="I'm not in a voice channel.")
            return

        if interaction.user.voice is None or interaction.user.voice.channel.id != player.channel.id:
            await msg.edit(content=f"You must be in {interaction.guild.voice_client.channel.mention} to use this.")
            return

        await player.stop(
            reason={
                'trigger': 'user_stop',
                'user': mc
            }
        )
        
        await msg.edit(content="Disconnected and queue cleared.")
    
    

async def setup(client: commands.Bot):
    await client.add_cog(MusicPlayer(client))