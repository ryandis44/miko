import discord
import mafic

from discord.ext.commands import Bot

class MikoPlayer(mafic.Player):
    def __init__(self, client: Bot, channel: discord.VoiceChannel) -> None:
        super().__init__(client, channel)
        self.client = client
        self.channel = channel
        
        self.queue: list[mafic.Track] = []
    
    
    
    async def skip(self) -> None: await super().stop()
    
    
    
    async def stop(self) -> None:
        self.queue.clear()
        await super().stop()
        await super().disconnect()



async def track_end(event: mafic.TrackEndEvent) -> None:
    assert isinstance(event.player, MikoPlayer)
    if len(event.player.queue) > 0: await event.player.play(event.player.queue.pop(0))
    else: await event.player.disconnect()