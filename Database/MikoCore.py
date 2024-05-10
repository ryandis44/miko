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
        self.user: MikoUser = None
        self.guild: MikoGuild = None
        
        
        
    def __str__(self) -> str: return f"MikoCore Object"
    
    
    
    async def user_ainit(self, user: discord.User|discord.Member, client: discord.Client) -> MikoUser:
        self.user = MikoUser(user=user, client=client)
        await self.user.ainit()
        if self.user.is_member:
            self.guild: MikoGuild = self.user.guild
            print(self.guild)
    
    
    
    async def guild_ainit(self, guild: discord.Guild, client: discord.Client) -> MikoGuild:
        self.guild = MikoGuild(guild=guild, client=client)
        await self.guild.ainit()
    
    
    
    # To reduce imports from multiple files, this function is used to access
    # tunables in files that already access MikoCore
    def tunables(self, key: str) -> str: return tunables(key)
    
    
    
    # Responsible for enforcing whether a feature/command is enabled globally,
    # or for a specific guild. If no guild is detected, the default 'ACTIVE'
    # profile is used
    @property
    def profile(self) -> PermissionProfile:
        if isinstance(self.guild, MikoGuild): return self.tunables(f'PERMS_PROFILE_{self.guild.profile_text}')
        return self.tunables('PERMS_PROFILE_ACTIVE')