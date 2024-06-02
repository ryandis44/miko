'''
Miko Music 3.0


File responsible for all visuals of the music player
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
    
    def __init__(self, mc: MikoCore, msg: discord.Message):
        self.mc = mc
        self.msg = msg
        super().__init__(timeout=mc.tunables('MUSIC_VIEW_TIMEOUT'))
        
        
        
    async def ainit(self) -> None:
        await self.prompt_sources()
    
    
    
    async def on_timeout(self) -> None:
        try: await self.msg.delete()
        except: pass
        
    
    
    def __add_source_buttons(self) -> None:
        for key, button in SOURCES.items():
            self.add_item(SourceButton(mc=self.mc, source=button))
    
    
    
    # Responsible for listing sources and prompting query
    async def prompt_sources(self) -> None:
        
        temp = []
        temp.append(
            "**Select a source to search from**.\n"
            "*URL must be from one of the\n"
            "below sources and can be a\n"
            "song, playlist, or album.*"
        )
        
        embed = discord.Embed(color=self.mc.tunables('GLOBAL_EMBED_COLOR'), description=''.join(temp))
        embed.set_author(name=f"{self.mc.guild.guild.me.name} Music", icon_url=self.mc.guild.guild.me.avatar)
        
        self.clear_items()
        self.__add_source_buttons()
        
        await self.msg.edit(embed=embed, view=self, content="# MUSIC PLAYER EARLY ALPHA. NOT FINAL PRODUCT. CURRENT COMMANDS: /play, /stop, /skip, /queue")
    
    
    
    # Responsible for selecting search results
    async def prompt_tracks(self, tracks: list[mafic.Track], source: dict) -> None:
        
        temp = []
        
        temp.append(
            f"This embed will expire in <t:{int(time.time()) + self.mc.tunables('MUSIC_VIEW_TIMEOUT')}:R>.\n\n"
            "`[`, `]`, `*`, `_` _removed from titles for formatting purposes_\n"
        )
        
        i = 0
        for track in tracks:
            i += 1
            dur = time_elapsed(int(track.length / 1000), ':')
            title = sanitize_track_name(track.title)
            author = sanitize_track_name(track.author)
            if len(title) > 23: title = f"{title[:20]}..."
            if len(author) > 23: author = f"{author[:20]}..."
            
            temp.append(
                f"{emojis_1to10(i-1)} {source['emoji']} [{title}]({track.uri}) by **`{author}`** 『`{dur}`』\n"
            )
            
            if i >= 10: break
        
        embed = discord.Embed(
            title='Search Results',
            color=self.mc.tunables('GLOBAL_EMBED_COLOR'),
            description=''.join(temp)
        )
        
        self.clear_items()
        self.__add_source_buttons()
        self.add_item(TrackSelectDropdown(tracks=tracks, source=source))
        
        await self.msg.edit(embed=embed, content=None, view=self)



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
        
        player: MikoPlayer = (
            interaction.guild.voice_client
        )
        
        match self.source['custom_id']:
            case "Spotify": search_type = SearchType.SPOTIFY_SEARCH
            case "Apple Music": search_type = SearchType.APPLE_MUSIC
            case "SoundCloud": search_type = SearchType.SOUNDCLOUD
            case "YouTube Music": search_type = SearchType.YOUTUBE_MUSIC
            case _: search_type = SearchType.YOUTUBE
        
        tracks = await player.fetch_tracks(self.query.value, search_type=search_type)
        
        if isinstance(tracks, Playlist): tracks = tracks.tracks
        if len(tracks) == 1: await player.enqueue(
            mc=self.mc,
            source=self.source if self.source['emoji'] is not None else SOURCES[tracks[0].source],
            tracks=tracks
        )
        else: await self.mmusic.prompt_tracks(
            tracks,
            self.source if self.source['emoji'] is not None else SOURCES[tracks[0].source]
        )



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
        
        player: MikoPlayer = (
            interaction.guild.voice_client
        )
        
        await player.enqueue(
            mc=self.view.mc,
            source=self.source['emoji'] if self.source['emoji'] is not None else SOURCES[self.tracks[int(self.values[0])].source]['emoji'],
            tracks=self.tracks[int(self.values[0]) - 1]
        )
        
        self.view.clear_items()
        emoji = self.source['emoji'] if self.source['emoji'] is not None else SOURCES[self.tracks[int(self.values[0])].source]['emoji']
        msg = await interaction.original_response()
        await msg.edit(
            content=(
                f"Added {emoji} **`{self.tracks[int(self.values[0])]}`** by **`{self.tracks[int(self.values[0])].author}`** to queue. "
                # f"View the active player in {self.view.mc.guild.music_channel.mention}."
            ),
            embed=None,
            view=self,
        )
        