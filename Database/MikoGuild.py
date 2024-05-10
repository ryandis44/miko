'''
This class is responsible for handling all guild data
'''



import discord
import logging

from Database.MySQL import AsyncDatabase
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoGuild:
    
    def __init__(self, guild: discord.Guild, client: discord.Client) -> None:
        self.guild: discord.Guild = guild
        self.client: discord.Client = client
        
        self.profile_text: str = "ACTIVE"
        self.emoji_id: int = None
        
        
        
    def __str__(self) -> str: return f"MikoGuild | {self.guild}"
        
        
        
    async def ainit(self, check_exists: bool = True) -> None:
        if check_exists: await self.__exists()
    
    
    
    async def __exists(self) -> None:
        __rawguild = await db.execute(
            f"SELECT profile,emoji_id FROM GUILDS WHERE guild_id='{self.guild.id}'"
        )
        
        if __rawguild == () or __rawguild is None:
            await db.execute(
                "INSERT INTO GUILDS (guild_id, name, owner_id, member_count) VALUES "
                f"('{self.guild.id}', '{self.guild.name}', '{self.guild.owner_id}', '{self.guild.member_count}')"
            )
            LOGGER.info(f"Added guild {self.guild.name} ({self.guild.id}) to database.")
            
        else:
            self.profile_text = __rawguild[0][0]
            self.emoji_id = __rawguild[0][1]
    
    
    
    def is_guild(self) -> bool: return True