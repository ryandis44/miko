'''
Miko Music 3.0

File responsible for all server-side UI elements of music player
'''


import asyncio
import discord
import logging
import mafic
import time

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
from misc.misc import time_elapsed, sanitize_track_name
from typing import List, Dict, Union
LOGGER = logging.getLogger()

class MikoPlayer(mafic.Player):
    def __init__(self, client: Bot, channel: discord.VoiceChannel) -> None:
        super().__init__(client, channel)
        self.client: Bot = client
        self.channel: discord.VoiceChannel = channel
        self.mc = MikoCore()
        self.msg: discord.Message = None
        self.__last_reposition: int = 0
        self.__lock = asyncio.Lock() # to prevent multiple players being sent at once
        
        # a list of dictionaries containing a MikoCore object, a source dict, and a mafic.Track object
        self.queue: List[Dict[str, Union[MikoCore, dict, mafic.Track]]] = []
        
        self.currently_playing = dict[Union[MikoCore, dict, mafic.Track]]
        
        self.volume: int = self.mc.tunables('MUSIC_PLAYER_DEFAULT_VOLUME')
    
    
    
    async def skip(self, mc: MikoCore) -> None:
        
        try:
            __title = sanitize_track_name(self.currently_playing['track'].title) # type: ignore
            __author = sanitize_track_name(self.currently_playing['track'].author) # type: ignore
            if len(__title) > self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH') + 3: __title = f"{__title[:self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH')]}..."
            if len(__author) > self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH') + 3: __author = f"{__author[:self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH')]}..."
            await self.mc.guild.music_channel.send(
                content=(
                    f"‼️ {mc.user.user.mention} skipped {self.currently_playing['source']} " # type: ignore
                    f"[{__title}]({self.currently_playing['track'].uri}) by **`{__author}`**" # type: ignore
                ),
                allowed_mentions=discord.AllowedMentions(users=False),
                suppress_embeds=True,
                silent=True
            )
        except Exception as e: LOGGER.error(f"Failed to notify music channel of skipped track: {self.mc.guild.guild} : {e}")
        
        await super().stop()
    
    
    
    async def play(self, data: Dict[str, Union[MikoCore, dict, mafic.Track]]) -> None:
        await super().play(data['track'])
        await super().set_volume(self.volume)
        data['start_time'] = int(time.time())
        data['paused_at'] = 0
        data['total_pause_time'] = 0
        self.currently_playing = data
        await self.heartbeat()
    
    
    
    async def set_volume(self, volume: int) -> None:
        self.volume = volume
        await super().set_volume(volume)
        await self.heartbeat()
    
    
    
    async def toggle_pause(self) -> None:
        
        if not self.paused:
            self.currently_playing['paused_at'] = int(time.time()) # type: ignore
        else:
            self.currently_playing['total_pause_time'] += int(time.time()) - self.currently_playing['paused_at'] # type: ignore
        
        await super().pause(not self.paused)
        await self.heartbeat()
    
    
    
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
                if len(self.queue) >= mc.tunables('MUSIC_PLAYER_QUEUE_CAPACITY'): break
                self.queue.append({
                    'user': mc,
                    'source': source,
                    'track': track
                })
        
        ########################################
        
        # Notify music channel of enqueued tracks
        try:
            if len(tracks) == 1:
                __title = sanitize_track_name(tracks[0].title)
                __author = sanitize_track_name(tracks[0].author)
                if len(__title) > self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH') + 3: __title = f"{__title[:self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH')]}..."
                if len(__author) > self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH') + 3: __author = f"{__author[:self.mc.tunables('MUSIC_PLAYER_MAX_LONG_STRING_LENGTH')]}..."
                
                await mc.guild.music_channel.send(
                    content=f"🎵 {mc.user.user.mention} added {source} [{__title}]({tracks[0].uri}) by **`{__author}`** to the queue.",
                    allowed_mentions=discord.AllowedMentions(users=False),
                    suppress_embeds=True,
                    silent=True
                )
            else:
                await mc.guild.music_channel.send(
                    content=f"🎶 {mc.user.user.mention} added {source} **`{len(tracks)} tracks`** to the queue.",
                    allowed_mentions=discord.AllowedMentions(users=False),
                    suppress_embeds=True,
                    silent=True
                )
        except Exception as e: LOGGER.error(f"Failed to notify music channel of enqueued tracks: {self.mc.guild.guild} : {e}")
        
        ########################################
        
        await self.heartbeat()
    
    
    
    async def stop(self, reason: dict = None) -> None:
        desc = f"Use {self.mc.tunables('SLASH_COMMAND_SUGGEST_PLAY')} to start playing music again."
        
        if self.msg.embeds:
            if self.msg.embeds[0].description == desc: return
        
        if not reason: reason = {'trigger': 'queue_complete'}
        
        match reason['trigger']:
            
            case 'queue_complete':
                name = "Queue complete"
                icon_url = self.client.user.avatar
            
            case 'user_stop':
                name = f"Playback stopped by {reason['user'].user.username}"
                icon_url = reason['user'].user.miko_avatar
            
            case 'disconnect_vc':
                name = "Disconnected from voice channel by an admin"
                icon_url = self.client.user.avatar
            
            case 'bot_restart':
                pass # TODO
        
        __embed = discord.Embed(
            color=self.mc.tunables('GLOBAL_EMBED_COLOR'),
            description=desc
        )
        __embed.set_author(
            name=name,
            icon_url=icon_url
        )
        
        try:
            self.msg = await self.msg.edit(
                content=None,
                embed=__embed,
                view=None
            )
        except: pass
        
        self.queue.clear()
        try: await super().stop()
        except: pass
        try: await super().disconnect(force=True)
        except: pass
    
    
    
    # Determines whether embed should be deleted and resent or
    # the current message should be edited
    async def heartbeat(self, reposition: bool = False) -> None:
        
        # Lock to prevent multiple players being sent at once
        async with self.__lock:
            try: self.mc.guild.profile_text
            except: await self.mc.guild_ainit(client=self.client, guild=self.channel.guild)
            
            if reposition:
                if self.__last_reposition + 5 <= int(time.time()): await asyncio.sleep(5)
                await self.reposition()
            
            else:
                try: await self.update_message()
                except: await self.reposition()
        
    
    
    async def update_message(self) -> None:
        await self.msg.edit(
            content=None,
            embed=self.__player_embed(),
            view=PlayerButtons(player=self)
        )
    
    
    
    async def reposition(self) -> None:
        
        if self.msg is not None:
            try: await self.msg.delete()
            except Exception as e: LOGGER.error(f"Failed to delete persistent player message: {self.mc.guild.guild} : {e}")
            
            
        self.__last_reposition = int(time.time())
        self.msg = await self.mc.guild.music_channel.send(
            content=None,
            embed=self.__player_embed(),
            view=PlayerButtons(player=self),
            silent=True
        )
    
    
    
    def __player_embed(self) -> discord.Embed:
        temp = []
        
        if self.paused and self.current is not None:
            temp.append(
                "# :pause_button: Playback is paused. Press the play button to resume.\n"
            )
        
        ########################################################
        
        # Currently playing section
        if self.current.stream:
            dur = "`🔴 LIVE`"
        else:
            dur = time_elapsed(int(self.current.length / 1000), ':')
            dur = f"`{dur} total`"
            
        __title = self.currently_playing['track'].title # type: ignore
        __author = self.currently_playing['track'].author # type: ignore
        if len(__title) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __title = f"{__title[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
        if len(__author) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __author = f"{__author[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
        
        temp.append(
            f"> {self.currently_playing['source']} [{sanitize_track_name(__title)}]({self.currently_playing['track'].uri}) by **`{sanitize_track_name(__author)}`**\n" # type: ignore
        )
        if not self.paused and self.current is not None:
            temp.append(
                f"> Started <t:{self.currently_playing['start_time'] + self.currently_playing['total_pause_time']}:R> ({dur})\n" # type: ignore
            )
        else:
            temp.append(
                f"> Playback paused (track length: {dur})\n" # type: ignore
            )
        
        temp.append(
            f"> Queued by {self.currently_playing['user'].user.user.mention}\n\n" # type: ignore
        )
        
        ########################################################
        
        # Queue section
        if len(self.queue) == 0:
            temp.append(f"Queue is empty. Queue more with {self.mc.tunables('SLASH_COMMAND_SUGGEST_PLAY')}\n")
        else:
            __queue = []
            i = 0
            for track in self.queue:
                if i < self.mc.tunables('MUSIC_PLAYER_MAX_VISIBLE_QUEUE_TRACKS'):
                    __title = track['track'].title
                    __author = track['track'].author
                    if len(__title) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __title = f"{__title[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
                    if len(__author) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __author = f"{__author[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
                    __queue.append(
                        f"{track['source']} [{sanitize_track_name(__title)}]({track['track'].uri}) by **`{sanitize_track_name(__author)}`**\n"
                    )
                i+=1
            
            len_queue = len(self.queue)
            temp.append(
                "__Up next:__\n"
                f"Queue length: **`{len_queue:,}`** track{'s' if len_queue > 1 else ''}\n"# • Total duration: **`{time_elapsed(int(total_milliseconds / 1000), ':')}`**\n"
                f"{''.join(__queue)}\n"
            )
            if len_queue > self.mc.tunables('MUSIC_PLAYER_MAX_VISIBLE_QUEUE_TRACKS'):
                temp.append(
                    f"...and **`{len_queue - self.mc.tunables('MUSIC_PLAYER_MAX_VISIBLE_QUEUE_TRACKS'):,}`** more\n"
                )
            
        ########################################################
            
        
        embed = discord.Embed(
            description=''.join(temp),
            color=self.mc.tunables('GLOBAL_EMBED_COLOR')
        )
        
        embed.set_author(
            name="Now Playing",
            icon_url=self.currently_playing['user'].user.user.avatar # type: ignore
        )
        
        try: embed.set_thumbnail(url=self.currently_playing['track'].artwork_url) # type: ignore
        except: embed.set_thumbnail(url=None)
        
        return embed



async def track_end(event: mafic.TrackEndEvent) -> None:
    assert isinstance(event.player, MikoPlayer)
    if len(event.player.queue) > 0:
        await event.player.play(event.player.queue.pop(0))
    else: await event.player.stop()



class PlayerButtons(discord.ui.View):
    def __init__(self, player: MikoPlayer) -> None:
        super().__init__(timeout=None)
        self.player = player
        
        # self.clear_items()
        self.add_item(VolumeDropdown(player=player))
        self.__button_presence()



    def __button_presence(self):
        pause_play = [x for x in self.children if x.custom_id=="pause_play"][0]
        stop = [x for x in self.children if x.custom_id=="stop_song"][0]
        next = [x for x in self.children if x.custom_id=="next_song"][0]
        vol = [x for x in self.children if x.custom_id=="volume"][0]
        queue = [x for x in self.children if x.custom_id=="full_queue"][0]

        stop.disabled = False
        pause_play.emoji = '⏸️' if not self.player.paused else '▶️'
        next.disabled = True if self.player.queue == [] else False
        vol.disabled = False
        queue.disabled = True if len(self.player.queue) <= self.player.mc.tunables('MUSIC_PLAYER_MAX_VISIBLE_QUEUE_TRACKS') else False
    


    @discord.ui.button(style=discord.ButtonStyle.red, emoji='⏹️', custom_id='stop_song', disabled=False, row=2)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.player.client)
        await interaction.response.edit_message()
        await self.player.stop(
            reason={
                'trigger': 'user_stop',
                'user': mc
            }
        )
    


    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='⏹️', custom_id='stop_song', disabled=False, row=2)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.player.client)
        await interaction.response.edit_message()
        await self.player.stop(
            reason={
                'trigger': 'user_stop',
                'user': mc
            }
        )



    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='⏸️', custom_id='pause_play', disabled=False, row=2)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message()
        await self.player.toggle_pause()
    
    
    
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='⏭️', custom_id='next_song', disabled=True, row=2)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.player.client)
        await interaction.response.edit_message()
        await self.player.skip(mc=mc)
    
    
    
    @discord.ui.button(style=discord.ButtonStyle.green, emoji=None, custom_id='full_queue', disabled=True, row=2, label="View Full Queue")
    async def full_queue(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await FullQueue(player=self.player).ainit(interaction=interaction)
    
    
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.player.client)
        if mc.user.bot_permission_level < 1: return False
        
        if interaction.user.voice is None or interaction.user.voice.channel.id != \
            interaction.guild.voice_client.channel.id:
                await interaction.response.send_message(
                    content=f"You must be in {interaction.guild.voice_client.channel.mention} to use this.",
                    ephemeral=True,
                    delete_after=10
                )
                return False
        return True
        


class VolumeDropdown(discord.ui.Select):
    def __init__(self, player: MikoPlayer) -> None:
        self.player = player
        red_warning = self.player.client.get_emoji(1074463168526561311)
        
        options = [
            discord.SelectOption(label='25%', value=25, emoji='🔈', default=player.volume==25),
            discord.SelectOption(label='50%', value=50, emoji='🔉', default=player.volume==50),
            discord.SelectOption(label='75%', value=75, emoji='🔉', default=player.volume==75),
            discord.SelectOption(label='100%', value=100, emoji='🔊', default=player.volume==100),
        ]
        
        if self.player.mc.tunables('MUSIC_PLAYER_EXTRA_VOLUME_OPTIONS'):
            options.extend([
                discord.SelectOption(label='200%. Some audio is distorted', value=200, emoji='🔊', default=player.volume==200),
                discord.SelectOption(label='300%. More audio is distorted', value=300, emoji='⚠', default=player.volume==300),
                discord.SelectOption(label='400%. Most audio is distorted', value=400, emoji='⚠', default=player.volume==400),
                discord.SelectOption(label='500%. Everything is distorted', value=500, emoji='⚠', default=player.volume==500),
                discord.SelectOption(label='1,000%. Why?', value=1000, emoji=red_warning, default=player.volume==1000),
            ])
        
        super().__init__(placeholder='Select a volume level...', custom_id="volume", options=options)
        self.player = player
    
    
    
    async def callback(self, interaction: discord.Interaction) -> None:
        try: await interaction.response.edit_message()
        except: pass
        await self.player.set_volume(int(self.values[0]))



class FullQueue(discord.ui.View):
    def __init__(self, player: MikoPlayer) -> None:
        self.mc = player.mc
        self.msg: discord.Message = None
        self.offset = 0
        self.player = player
        super().__init__(timeout=self.mc.tunables('MUSIC_VIEW_TIMEOUT'))
        self.button_presence()
    
    
    
    async def on_timeout(self) -> None:
        try: await self.msg.delete()
        except: pass
    
    
    
    async def ainit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            content=self.mc.tunables('LOADING_EMOJI'),
            ephemeral=True
        )
        self.msg = await interaction.original_response()
        await self.response()
        
    
    
    def button_presence(self) -> None:
        front = [x for x in self.children if x.custom_id=="front"][0]
        back = [x for x in self.children if x.custom_id=="back"][0]
        next = [x for x in self.children if x.custom_id=="next"][0]
        end = [x for x in self.children if x.custom_id=="end"][0]

        queue_len = len(self.player.queue)
        
        if self.offset > 0:
            front.disabled = False
            back.disabled = False
        else:
            front.disabled = True
            back.disabled = True
        
        if queue_len > self.offset + self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'):
            next.disabled = False
            end.disabled = False
        else:
            next.disabled = True
            end.disabled = True
    
    
    
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='⏮️', custom_id='front', disabled=True)
    async def front(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.offset = 0
        await interaction.response.edit_message()
        await self.response()
    
    
    
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='◀️', custom_id='back', disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        # If 8 <= 10
        if self.offset <= self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'): self.offset = 0
        # If 8 > 8 - 10
        elif self.offset > self.offset - self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'): self.offset -= self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS')
        else: return
        await interaction.response.edit_message()
        await self.response()
    
    
    
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='▶️', custom_id='next', disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        queue_len = len(self.player.queue)
        # If 17 > 0 + 20 == False
        if queue_len > self.offset + (self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS') * 2): self.offset += self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS')
        # If 17 <= 0 + 20 == True
        elif queue_len <= self.offset + (self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS') * 2): self.offset = queue_len - self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS')
        else: return
        await interaction.response.edit_message()
        await self.response()
    
    
    
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='⏭️', custom_id='end', disabled=True)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.offset = len(self.player.queue) - self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS')
        await interaction.response.edit_message()
        await self.response()
    
    
    
    async def response(self) -> None:
        self.button_presence()
        await self.msg.edit(
            content=None,
            embed=self.__embed(),
            view=self
        )
    
    
    
    def __embed(self) -> discord.Embed:
        temp = []
        
        temp.append(                        
            f"> **This embed will**\n> **expire <t:{int(time.time()) + self.mc.tunables('MUSIC_VIEW_TIMEOUT')}:R>.**\n\n"
        )
        
        total_milliseconds = 0
        for track in self.player.queue: total_milliseconds += track['track'].length
        queue_len = len(self.player.queue)
        __queue = []
        i = 0
        while True:
            if i >= queue_len: break
            __title = self.player.queue[i + self.offset]['track'].title
            __author = self.player.queue[i + self.offset]['track'].author
            if len(__title) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __title = f"{__title[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            if len(__author) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __author = f"{__author[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            
            __queue.append(
                f"`{i + self.offset + 1}.` {self.player.queue[i + self.offset]['source']} "
                f"[{__title}]({self.player.queue[i + self.offset]['track'].uri}) "
                f"by **`{__author}`** • {self.player.queue[i + self.offset]['user'].user.user.mention}\n"
            )
        
            i+=1
            if i >= self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'): break
        
        temp.append(
            f"Queue duration: `{time_elapsed(int(total_milliseconds / 1000), ':')}`\n\n"
            "__Full Queue__:\n"
            f"{''.join(__queue)}\n"
        )
        
        embed = discord.Embed(
            description=''.join(temp),
            color=self.mc.tunables('GLOBAL_EMBED_COLOR')
        )
        
        if i > self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'):
            embed.set_footer(
                text=f"Showing tracks {self.offset + 1:,} - {self.offset + self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'):,} of {queue_len:,}"
            )
        elif len(self.player.queue) > 0:
            embed.set_footer(
                text=f"Showing tracks {self.offset + 1:,} - {queue_len:,} of {queue_len:,}"
            )
        else:
            embed.set_footer(
                text="Showing tracks 0 - 0 of 0"
            )
        
        return embed