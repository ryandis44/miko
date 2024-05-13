'''
This class is responsible for handling all user data
'''



import discord
import logging
import time

from Database.MikoGuild import MikoGuild
from Database.MikoUser import MikoUser
from Database.MySQL import AsyncDatabase
from Database.tunables import tunables, PermissionProfile
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoCore:
    
    def __init__(self) -> None:
        self.user = MikoUser()
        self.guild = MikoGuild()
        
        
        
    def __str__(self) -> str: return f"MikoCore Object"
    
    
    
    # Initialize MikoUser and MikoGuild if the user is also a member of a guild (not a DM)
    async def user_ainit(self, user: discord.User|discord.Member, client: discord.Client) -> MikoUser:
        await self.user.ainit(user=user, client=client)
        if self.user.is_member: self.guild: MikoGuild = self.user.guild
    
    
    
    async def guild_ainit(self, guild: discord.Guild, client: discord.Client) -> MikoGuild:
        await self.guild.ainit(guild=guild, client=client)
    
    
    
    # To reduce imports from multiple files, this function is used to access
    # tunables in files that already access MikoCore
    def tunables(self, key: str) -> str: return tunables(key)
    
    
    
    # Responsible for enforcing whether a feature/command is enabled globally,
    # or for a specific guild. If no guild is detected, the default 'ACTIVE'
    # profile is used
    @property
    def profile(self) -> PermissionProfile:
        __profile = self.tunables(f'PERMS_PROFILE_{self.guild.profile_text}')
        if __profile is not None: return __profile
        else:
            LOGGER.warning(f"Guild profile '{self.guild.profile_text}' for guild {self.guild.guild.name} ({self.guild.guild.id}) not found. Using default 'ACTIVE' profile")
            return self.tunables('PERMS_PROFILE_ACTIVE')