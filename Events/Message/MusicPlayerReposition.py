'''
Big emojis. Takes the png of the emoji, enlarges it,
and sends it in an embed to make the emoji bigger
'''



import logging

from Database.MikoCore import MikoCore
from cogs_cmd_on_ready.MusicPlayer.Backend import MikoPlayer
LOGGER = logging.getLogger()

async def reposition_music_player(mc: MikoCore) -> bool:
    if mc.profile.feature_enabled('MUSIC_CHANNEL') != 1: return False
    
    player: MikoPlayer = (mc.guild.guild.voice_client)
    
    if player is None or mc.message.message.channel.id != mc.guild.music_channel.id: return False
    
    # Delete any messages not from Miko while playing music
    if mc.message.message.author != mc.message.client.user and player.current:
        try:
            await mc.message.message.delete()
            return True
        except: pass
    
    # Reposition music player if message is from Miko but not the
    # active music player embed
    try:
        if not mc.message.message.content and mc.message.message.embeds:
            if mc.message.message.embeds[0].author.name == "Now Playing": return False
        await player.heartbeat(reposition=True)
        return True
    except: pass