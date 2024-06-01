'''
Miko Music 3.0


File responsible for all visuals of the music player
'''



import discord

from Database.MikoCore import MikoCore
from Database.tunables import tunables
from cogs_cmd_on_ready.MusicPlayer.PlayerClass import MikoPlayer
from mafic import SearchType, Playlist

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
        super().__init__(timeout=mc.tunables('GLOBAL_VIEW_TIMEOUT'))
        
        
        
    async def ainit(self) -> None:
        await self.prompt_sources()
        
    
    
    def __add_source_buttons(self) -> None:
        for key, button in SOURCES.items():
            self.add_item(SourceButton(mc=self.mc, source=button))
    
    
    
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
        await interaction.response.send_modal(SearchModal(mc=self.mc, source=self.source))



class SearchModal(discord.ui.Modal):
    def __init__(self, mc: MikoCore, source: dict) -> None:
        self.mc = mc
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
            await channel.connect(cls=MikoPlayer)
        
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
        
        if player.current: player.queue.append(tracks[0])
        else: await player.play(tracks[0])
        
        if self.source['emoji'] is None: source_emoji = SOURCES[tracks[0].source]['emoji']
        else: source_emoji = self.source['emoji']
        
        await interaction.channel.send(
            f"Added {source_emoji} `{tracks[0].title}` by `{tracks[0].author}` to queue."
        )
        
        