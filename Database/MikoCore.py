'''
This class is responsible for handling all user data
'''



import discord
import logging
import time

from Database.MikoGuild import MikoGuild
from Database.MikoMessage import MikoMessage
from Database.MikoTextChannel import MikoTextChannel
from Database.MikoUser import MikoUser
from Database.MySQL import AsyncDatabase
from Database.tunables import tunables, PermissionProfile
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoCore:
    
    def __init__(self) -> None:
        self.user = MikoUser()
        self.guild = MikoGuild()
        self.channel = MikoTextChannel()
        self.message = MikoMessage()
        
        self.threads = [discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.news_thread]
        
        
        
    def __str__(self) -> str: return f"MikoCore Object"
    
    
    
    '''
    Logic below:
    - Initialize MikoUser
    - If the user is a member, initialize MikoGuild
    '''
    async def user_ainit(self, user: discord.User|discord.Member, client: discord.Client, check_exists: bool = True) -> MikoUser:
        await self.user.ainit(user=user, client=client, check_exists=check_exists)
        if self.user.is_member: self.guild: MikoGuild = self.user.guild
    
    
    
    async def guild_ainit(self, guild: discord.Guild, client: discord.Client, check_exists: bool = True) -> MikoGuild:
        await self.guild.ainit(guild=guild, client=client, check_exists=check_exists)
        
    
    
    async def channel_ainit(self, channel: discord.TextChannel, client: discord.Client, check_exists: bool = True) -> MikoTextChannel:
        await self.channel.ainit(channel=channel, client=client, check_exists=check_exists)
    
    
    
    '''
    Logic below:
    - Initialize MikoMessage
    - Initialize MikoUser (and MikoGuild, handled in user_ainit, if user is also a member)
    - Initialize MikoTextChannel (if user is a member)
    '''
    async def message_ainit(self, message: discord.Message, client: discord.Client) -> None:
        await self.message.ainit(message=message, client=client)
        await self.user_ainit(user=message.author, client=client)
        if self.user.is_member: await self.channel_ainit(channel=message.channel, client=client)
    
    
    
    # To reduce imports from multiple files, this function is used to access
    # tunables in files that already access MikoCore
    def tunables(self, key: str) -> str: return tunables(key)
    
    
    
    # Responsible for enforcing whether a feature/command is enabled globally,
    # or for a specific guild. If no guild is detected, the default 'ACTIVE'
    # profile is used
    @property
    def profile(self) -> PermissionProfile:
        __profile: PermissionProfile = self.tunables(f'PERMS_PROFILE_{self.guild.profile_text}')
        if __profile is not None:
            __profile.inject_guild(self.guild.guild_settings)
            return __profile
        else:
            LOGGER.warning(f"Guild profile '{self.guild.profile_text}' for guild {self.guild.guild.name} ({self.guild.guild.id}) not found. Using default 'ACTIVE' profile")
            return self.tunables('PERMS_PROFILE_ACTIVE')