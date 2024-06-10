'''
Miko Music 3.0


File responsible for all client-sided UI elements of the music player
'''



import discord
import time
import mafic

from Database.MikoCore import MikoCore
from Database.tunables import tunables
from cogs_cmd_on_ready.MusicPlayer.Backend import MikoPlayer
from mafic import SearchType, Playlist
from misc.misc import emojis_1to10, sanitize_track_name, time_elapsed

SOURCES = {
            "url": {
                "label": "URL",
                "emoji": None,
                "custom_id": "URL",
                "row": 1,
                "disabled": tunables('MUSIC_PLAYER_URL_BUTTON_DISABLED')
            },
            "youtube": {
                "label": None,
                "emoji": tunables('YOUTUBE_EMOJI'),
                "custom_id": "YouTube",
                "row": 1,
                "disabled": tunables('MUSIC_PLAYER_YOUTUBE_BUTTON_DISABLED')
            },
            "spotify": {
                "label": None,
                "emoji": tunables('SPOTIFY_EMOJI'),
                "custom_id": "Spotify",
                "row": 1,
                "disabled": tunables('MUSIC_PLAYER_SPOTIFY_BUTTON_DISABLED')
            },
            "applemusic": {
                "label": None,
                "emoji": tunables('APPLEMUSIC_EMOJI'),
                "custom_id": "Apple Music",
                "row": 2,
                "disabled": tunables('MUSIC_PLAYER_APPLEMUSIC_BUTTON_DISABLED')
            },
            "youtubemusic": {
                "label": None,
                "emoji": tunables('YOUTUBEMUSIC_EMOJI'),
                "custom_id": "YouTube Music",
                "row": 2,
                "disabled": tunables('MUSIC_PLAYER_YOUTUBEMUSIC_BUTTON_DISABLED')
            },
            "soundcloud": {
                "label": None,
                "emoji": tunables('SOUNDCLOUD_EMOJI'),
                "custom_id": "SoundCloud",
                "row": 2,
                "disabled": tunables('MUSIC_PLAYER_SOUNDCLOUD_BUTTON_DISABLED')
            },
        }

class MikoMusic(discord.ui.View):
    
    def __init__(self, mc: MikoCore, msg: discord.Message = None, interaction: discord.Interaction = None):
        self.mc = mc
        self.msg = msg
        self.player: MikoPlayer = None
        super().__init__(timeout=mc.tunables('MUSIC_VIEW_TIMEOUT'))
        
        
        
    async def ainit(self) -> None:
        await self.prompt_sources()
    
    
    
    async def on_timeout(self) -> None:
        try: await self.msg.delete()
        except: pass
        
        # TODO
        # Ensure Miko does not stay in voice chat indefinitely
        # if no tracks are enqueued
        # try:
        #     if not self.player.current:
        #         await self.player.stop()
        # except: pass
        
    
    
    def add_source_buttons(self) -> None:
        for key, button in SOURCES.items():
            self.add_item(SourceButton(mc=self.mc, source=button))
    
    
    
    def __sources_embed(self) -> discord.Embed:
        temp = []
        temp.append(
            f"> **This embed will**\n> **expire <t:{int(time.time()) + self.mc.tunables('MUSIC_VIEW_TIMEOUT')}:R>.**\n\n"
            f"Max queue length: **`{self.mc.tunables('MUSIC_PLAYER_QUEUE_CAPACITY'):,}`** tracks\n\n"
            "**Select a source to search from**.\n"
            "*URL must be from one of the\n"
            "below sources and can be a\n"
            "song, playlist, or album.*"
        )
        
        embed = discord.Embed(color=self.mc.tunables('GLOBAL_EMBED_COLOR'), description=''.join(temp))
        embed.set_author(name=f"{self.mc.guild.guild.me.name} Music", icon_url=self.mc.guild.guild.me.avatar)
        return embed
    
    
    
    # Responsible for listing sources and prompting query
    async def prompt_sources(self) -> None:
        
        self.clear_items()
        self.add_source_buttons()
        
        await self.msg.edit(embed=self.__sources_embed(), view=self, content=None)
    
    
    
    # Responsible for selecting search results
    async def prompt_tracks(self, query: str, tracks: list[mafic.Track], source: dict) -> None:
        
        temp = []
        
        temp.append(
            f"> **This embed will**\n> **expire <t:{int(time.time()) + self.mc.tunables('MUSIC_VIEW_TIMEOUT')}:R>.**\n\n"
        )
        
        if isinstance(tracks, Playlist):
            __playlist_name = sanitize_track_name(tracks.name)
            if len(__playlist_name) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __playlist_name = f"{__playlist_name[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            temp.append(f"**Top {self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS')} tracks from** `{__playlist_name}`\n")
        else:
            __query = sanitize_track_name(query)
            if len(query) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __query = f"{__query[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            temp.append(f"**Top {self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS')} tracks for** `{__query}`\n")
        
        temp.append(
            "`[`, `]`, `*`, `_` _removed from titles for formatting purposes_\n"
        )
        
        if isinstance(tracks, Playlist): all_tracks = tracks.tracks
        else: all_tracks = tracks
        
        i = 0
        for track in all_tracks:
            i += 1
            dur = time_elapsed(int(track.length / 1000), ':')
            title = sanitize_track_name(track.title)
            author = sanitize_track_name(track.author)
            if len(title) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: title = f"{title[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            if len(author) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: author = f"{author[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            
            temp.append(
                f"{emojis_1to10(i-1)} {source['emoji']} [{title}]({track.uri}) by **`{author}`** 『`{dur}`』\n"
            )
            
            if i >= self.mc.tunables('MUSIC_PLAYER_MAX_VIEWABLE_OPTIONS'): break
        
        self.clear_items()
        self.add_source_buttons()
        if isinstance(tracks, Playlist): # for whole playlist/album
            if i < len(tracks.tracks):
                temp.append(
                    f"\n...and **`{len(tracks.tracks) - i:,}`** more in this playlist\n"
                )
            self.add_item(EnqueueTracksButton(mc=self.mc, tracks=tracks.tracks, source=source))
            __shuffle_button = EnqueueTracksButton(mc=self.mc, tracks=tracks.tracks, source=source)
            __shuffle_button.label = f"{__shuffle_button.label}, but shuffled"
            __shuffle_button.custom_id = "shuffle_tracks"
            __shuffle_button.row = 4
            self.add_item(__shuffle_button)
                
        else: self.add_item(TrackSelectDropdown(tracks=tracks, source=source)) # for single track
        
        embed = discord.Embed(
            title='Search Results',
            color=self.mc.tunables('GLOBAL_EMBED_COLOR'),
            description=''.join(temp)
        )
        
        await self.msg.edit(embed=embed, content=None, view=self)

    
    
    async def notify_enqueued(self, all_tracks: list[mafic.Track], source: dict) -> None:
        temp = []
        
        if len(all_tracks) > 1:
            temp.append(f"Added {source['emoji']} **`{len(all_tracks):,} track{'s' if len(all_tracks) > 1 else ''}` to queue**\n")
        
        else:
            __title = sanitize_track_name(all_tracks[0].title)
            __author = sanitize_track_name(all_tracks[0].author)
            if len(__title) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __title = f"{__title[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            if len(__author) > self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH') + 3: __author = f"{__author[:self.mc.tunables('MUSIC_PLAYER_MAX_STRING_LENGTH')]}..."
            temp.append(
                f"Added {source['emoji']} [{__title}]({all_tracks[0].uri}) by **`{__author}`** to queue\n"
            )
        
        temp.append(
            f"View the active player in {self.mc.guild.music_channel.mention}."
            "\n\n"
            "**Optionally queue more tracks below!**"
        )
        
        await self.msg.edit(
            embed=self.__sources_embed(),
            view=self,
            content=''.join(temp)
        )



class SourceButton(discord.ui.Button):
    def __init__(self, mc: MikoCore, source: dict):
        self.mc = mc
        self.source = source
        super().__init__(
            style=discord.ButtonStyle.gray,
            label=source['label'],
            emoji=source['emoji'],
            custom_id=source['custom_id'],
            row=source['row'],
            disabled=source['disabled']
        )
        
    
    
    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(SearchModal(mc=self.mc, source=self.source, mmusic=self.view))



class EnqueueTracksButton(discord.ui.Button):
    def __init__(self, mc: MikoCore, tracks: list[mafic.Track], source: dict):
        self.mc = mc
        self.source = source
        self.tracks = tracks
        super().__init__(
            style=discord.ButtonStyle.green,
            label=f"Add {len(tracks):,} tracks to queue",
            emoji=None,
            custom_id="enqueue_tracks",
            row=3,
            disabled=False
        )
        
    
    
    async def callback(self, interaction: discord.Interaction) -> None:
        try: await interaction.response.edit_message()
        except: pass
        self.view.player = (interaction.guild.voice_client)
        
        if self.custom_id == "shuffle_tracks":
            import random
            random.shuffle(self.tracks)
        
        await self.view.player.enqueue(
            mc=self.mc,
            source=self.source['emoji'] if self.source['emoji'] is not None else SOURCES[self.tracks[0].source]['emoji'],
            tracks=self.tracks
        )
        
        self.view.clear_items()
        self.view.add_source_buttons()
        await self.view.notify_enqueued(self.tracks, self.source)



class SearchModal(discord.ui.Modal):
    def __init__(self, mc: MikoCore, source: dict, mmusic: MikoMusic) -> None:
        self.mc = mc
        self.mmusic = mmusic
        self.source = source
        super().__init__(title=f"{source['custom_id']} Search", custom_id="search_modal")
      
      
        
    query = discord.ui.TextInput(
        label="Search for something",
        min_length=1
    )
    
    
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message()
        
        if not interaction.guild.voice_client:
            channel = interaction.user.voice.channel
            await channel.connect(cls=MikoPlayer, self_deaf=True)
        
        self.mmusic.player = (
            interaction.guild.voice_client
        )
        
        match self.source['custom_id']:
            case "Spotify": search_type = SearchType.SPOTIFY_SEARCH
            case "Apple Music": search_type = SearchType.APPLE_MUSIC
            case "SoundCloud": search_type = SearchType.SOUNDCLOUD
            case "YouTube Music": search_type = SearchType.YOUTUBE_MUSIC
            case _: search_type = SearchType.YOUTUBE
        
        await self.mmusic.msg.edit(content=self.mc.tunables('LOADING_EMOJI'), embed=None, view=None)
        
        try: tracks = await self.mmusic.player.fetch_tracks(self.query.value, search_type=search_type)
        except Exception as e:
            await self.mmusic.msg.edit(
                embed=discord.Embed(
                    title="An error occurred, please try again",
                    color=self.mc.tunables('GLOBAL_EMBED_COLOR'),
                    description=(
                        f"> **This embed will**\n> **expire <t:{int(time.time()) + self.mc.tunables('MUSIC_VIEW_TIMEOUT')}:R>.**\n\n"
                        f"An error occurred while searching for **`{self.query.value}`**\n\n"
                        "```py\n"
                        f"Error: {e}"
                        "```\n\n"
                        "If trying to queue a YouTube Music radio, start the radio and paste the "
                        "URL when it has `/watch?v=...` in the address bar (instead of `/playlist?list=...`)."
                    )
                ),
                content=None,
                view=self.mmusic
            )
            return
        
        if isinstance(tracks, Playlist): all_tracks = tracks.tracks
        else: all_tracks = tracks


        # TODO fix bug that causes source to be incorrect when
        # pasting a link into any search other than URL


        ########################################
        # Determine source
        if self.source['emoji'] is not None: __source = self.source
        else: __source = SOURCES[all_tracks[0].source]
        
        # Correct wavelink source recognition via URL
        if __source == SOURCES["youtube"]:
            if "music.youtube.com" in self.query.value:
                __source = SOURCES["youtubemusic"]
        ########################################

        
        if len(all_tracks) == 1:
            await self.mmusic.player.enqueue(
                mc=self.mc,
                source=__source['emoji'],
                tracks=all_tracks
            )
            self.mmusic.clear_items()
            self.mmusic.add_source_buttons()
            await self.mmusic.notify_enqueued(all_tracks, __source)
            
        elif len(all_tracks) == 0:
            await self.mmusic.msg.edit(
                embed=discord.Embed(
                    title="No results found, please try again",
                    color=self.mc.tunables('GLOBAL_EMBED_COLOR'),
                    description=(
                        f"> **This embed will**\n> **expire <t:{int(time.time()) + self.mc.tunables('MUSIC_VIEW_TIMEOUT')}:R>.**\n\n"
                        f"No tracks found for **`{self.query.value}`**."
                    )
                ),
                content=None,
                view=self.mmusic
            )
            
        else: await self.mmusic.prompt_tracks(self.query.value, tracks, __source)



class TrackSelectDropdown(discord.ui.Select):
    def __init__(self, tracks: list[mafic.Track], source) -> None:
        self.tracks = tracks
        self.source = source
        
        options = []
        i = 0
        for track in tracks:
            i += 1
            title = sanitize_track_name(track.title)
            author = sanitize_track_name(track.author)
            if len(title) > 85: title = f"{title[:90]}..."
            if len(author) > 85: author = f"{author[:90]}..."
            options.append(
                discord.SelectOption(
                    label=title,
                    description=author,
                    value=i,
                    emoji=emojis_1to10(i-1)
                )
            )
            if i >= 10: break
        
        super().__init__(
            placeholder="Select a track",
            max_values=1,
            min_values=1,
            options=options,
            row=3
        )
    
    
    
    async def callback(self, interaction: discord.Interaction) -> None:
        try: await interaction.response.edit_message()
        except: pass
        
        if not interaction.guild.voice_client:
            channel = interaction.user.voice.channel
            await channel.connect(cls=MikoPlayer, self_deaf=True)
        
        self.view.player = (
            interaction.guild.voice_client
        )
        
        await self.view.player.enqueue(
            mc=self.view.mc,
            source=self.source['emoji'] if self.source['emoji'] is not None else SOURCES[self.tracks[int(self.values[0])].source]['emoji'],
            tracks=self.tracks[int(self.values[0]) - 1]
        )
        
        self.view.clear_items()
        self.view.add_source_buttons()
        await self.view.notify_enqueued([self.tracks[int(self.values[0]) - 1]], self.source)
        