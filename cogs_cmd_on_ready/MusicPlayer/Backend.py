import asyncio
import discord
import logging
import mafic
import time

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
from misc.misc import time_elapsed
from typing import List, Dict, Union
LOGGER = logging.getLogger()

class MikoPlayer(mafic.Player):
    def __init__(self, client: Bot, channel: discord.VoiceChannel) -> None:
        super().__init__(client, channel)
        self.client = client
        self.channel = channel
        
        # a list of dictionaries containing a MikoCore object and a mafic.Track object
        self.queue: List[Dict[str, Union[MikoCore, dict, mafic.Track]]] = []
        self.persistent_player = PersistentPlayer(client=client, channel=channel, player=self)
        
        self.currently_playing = dict[Union[MikoCore, dict, mafic.Track]]
    
    
    
    async def skip(self) -> None: await super().stop()
    
    
    
    async def play(self, data: Dict[str, Union[MikoCore, dict, mafic.Track]]) -> None:
        await super().play(data['track'])
        self.currently_playing = data
        await self.persistent_player.ainit()
    
    
    
    async def enqueue(self, mc: MikoCore, source: dict, tracks: list[mafic.Track]) -> None:
        
        if type(tracks) is not list:
            tracks = [tracks]
        
        for i, track in enumerate(tracks):
            
            # If the player is not currently playing anything, play the first track.
            # Only consider this for the first iteration of the loop, as the player
            # is guaranteed to be playing something after the first iteration.
            if i == 0 and self.current is None:
                await self.play(
                    data={
                        'user': mc,
                        'source': source,
                        'track': track
                    }
                )
            
            # If the player is currently playing something, add the track to the queue
            else:
                self.queue.append([{
                    'user': mc,
                    'source': source,
                    'track': track
                }])
    
    
    
    async def stop(self) -> None:
        self.queue.clear()
        await super().stop()
        await super().disconnect()



async def track_end(event: mafic.TrackEndEvent) -> None:
    assert isinstance(event.player, MikoPlayer)
    if len(event.player.queue) > 0: await event.player.play(event.player.queue.pop(0))
    else: await event.player.disconnect()



class PersistentPlayer(discord.ui.View):
    def __init__(self, client: Bot, channel: discord.VoiceChannel, player: MikoPlayer) -> None:
        self.mc = MikoCore()
        super().__init__(timeout=None)
        self.client = client
        self.player = player
        self.channel = channel
        self.msg: discord.Message = None
        self.__last_reposition: int = 0
    
    
    
    async def ainit(self) -> None:
        await self.mc.guild_ainit(client=self.client, guild=self.channel.guild)
        await self.reposition()
        
        
    
    async def reposition(self) -> None:
        
        # Only reposition player once every 5 seconds to avoid rate limit
        if self.__last_reposition + 5 >= int(time.time()):
            await asyncio.sleep(5)
        
        if self.msg is not None:
            try: await self.msg.delete()
            except Exception as e: LOGGER.error(f"Failed to delete persistent player message: {e}")
            
        self.msg = await self.mc.guild.music_channel.send(
            content=None,
            embed=await self.__player_embed(),
            view=self
        )
        self.__last_reposition = int(time.time())
    
    
    
    async def __player_embed(self) -> discord.Embed:
        temp = []
        
        # Currently playing section
        dur = time_elapsed(int(self.player.current.length / 1000), ':')
        temp.append(
            f"\u200b \u200b├─ Title: **`{self.player.currently_playing['track'].title}`**\n" # type: ignore
            f"\u200b \u200b├─ By: **`{self.player.currently_playing['track'].author}`**\n" # type: ignore
            f"\u200b \u200b├─ Timestamp: **`0 / {dur}`**\n"
            f"\u200b \u200b└─ Source: [WIP]\n"
        )
        
        temp.append(
            f"{self.player.currently_playing['user'].user.first_join}" # type: ignore
        )
        
        # Queue section
        # if len(self.player.queue) == 0:
        #     temp.append("\n# Queue is empty.")
        # else:
        #     total_milliseconds = 0
        #     for track in self.player.queue:
        #         total_milliseconds += track['track'].length
        
        embed = discord.Embed(
            title=":musical_note: Now Playing",
            description=''.join(temp),
            color=self.mc.tunables('GLOBAL_EMBED_COLOR')
        )
        
        '''
        Set embed.set_author et al.
        '''
        
        return embed