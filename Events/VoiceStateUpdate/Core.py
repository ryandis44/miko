'''
Calling file for all message events
'''



import discord
import logging

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
LOGGER = logging.getLogger()

async def caller(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_VOICE_STATE_UPDATE'): return
    
    # Stop player only if Miko left the voice channel
    if member.id == client.user.id:
        player = (member.guild.voice_client)
        if before.channel is not None and after.channel is None:
            await player.stop(
                reason={
                    'trigger': 'disconnect_vc'
                }
            )