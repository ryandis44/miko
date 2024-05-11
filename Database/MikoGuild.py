'''
This class is responsible for handling all guild data
'''



import discord
import logging

from Database.MySQL import AsyncDatabase
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoGuild:
    
    def __init__(self) -> None:
        self.guild: discord.Guild = None
        self.client: discord.Client = None
        
        self.profile_text: str = "ACTIVE"
        self.emoji_id: int = None
        
        
        
    def __str__(self) -> str: return f"MikoGuild | {self.guild}"
        
        
        
    async def ainit(self, guild: discord.Guild, client: discord.Client, check_exists: bool = True) -> None:
        self.guild = guild
        self.client = client
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
    
    
    
###########################################################################################################################
    
    
    
    @property
    async def ymca_green_book_announce_channel(self) -> discord.TextChannel:
        __channel_id = await db.execute(
            f"SELECT ymca_green_book_announce_channel FROM GUILD_SETTINGS WHERE guild_id='{self.guild.id}'"
        )
        return self.guild.get_channel(int(__channel_id)) if __channel_id is not None or __channel_id == () else None