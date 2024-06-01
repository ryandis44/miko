import discord
import mafic

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot

class MikoPlayer(mafic.Player):
    def __init__(self, client: Bot, channel: discord.VoiceChannel) -> None:
        super().__init__(client, channel)
        self.client = client
        self.channel = channel
        
        self.queue: list[mafic.Track] = []
        self.persistent_player = PersistentPlayer(client=client, channel=channel)
    
    
    
    async def skip(self) -> None: await super().stop()
    
    
    
    async def play(self, track: mafic.Track, start_time: int = None, end_time: int = None, volume: int = None, replace: bool = True, pause: bool = None) -> None:
        await super().play(track=track, start_time=start_time, end_time=end_time, volume=volume, replace=replace, pause=pause)
        await self.persistent_player.ainit()
    
    
    async def stop(self) -> None:
        self.queue.clear()
        await super().stop()
        await super().disconnect()



async def track_end(event: mafic.TrackEndEvent) -> None:
    assert isinstance(event.player, MikoPlayer)
    if len(event.player.queue) > 0: await event.player.play(event.player.queue.pop(0))
    else: await event.player.disconnect()



class PersistentPlayer(discord.ui.View):
    def __init__(self, client: Bot, channel: discord.VoiceChannel) -> None:
        self.mc = MikoCore()
        self.client = client
        self.channel = channel
    
    
    
    async def ainit(self) -> None:
        await self.mc.guild_ainit(client=self.client, guild=self.channel.guild)