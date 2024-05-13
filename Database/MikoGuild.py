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
        
        # self.profile_text: str = "ACTIVE"
        # self.emoji_id: int = None
        # self.ymca_green_book_announce_channel: discord.TextChannel|None = None
        
        
        
    def __str__(self) -> str: return f"MikoGuild | {self.guild}"
        
        
        
    async def ainit(self, guild: discord.Guild, client: discord.Client, check_exists: bool = True) -> None:
        self.guild = guild
        self.client = client
        if check_exists: await self.__exists()
    
    
    
    async def reinit(self) -> None:
        await self.ainit(guild=self.guild, client=self.client)
    
    
    
    async def __exists(self) -> None:
        
        # Check if guild exists
        __rawguild = await db.execute(
            f"SELECT profile,emoji_id,name,owner_id,member_count FROM GUILDS WHERE guild_id='{self.guild.id}'"
        )
        if __rawguild == [] or __rawguild is None:
            await db.execute(
                "INSERT INTO GUILDS (guild_id, name, owner_id, member_count) VALUES "
                f"('{self.guild.id}', '{self.guild.name}', '{self.guild.owner_id}', '{self.guild.member_count}')"
            )
            LOGGER.info(f"Added guild {self.guild.name} ({self.guild.id}) to database.")
            
        else:
            # Since we requested the guild from the database, and we know it exists,
            # we can assign guild attributes from the database here.
            self.profile_text = __rawguild[0][0]
            self.emoji_id = __rawguild[0][1]
            
            await self.__update_database(__rawguild)
            
            # Check if guild settings exist. Request settings from
            # database twice only if it does not exist. Else,
            # request settings only once.
            __db_string = (
                "SELECT ymca_green_book_announce_channel,music_channel "
                f"FROM GUILD_SETTINGS WHERE guild_id='{self.guild.id}'"
            )
            __rawguild_settings = await db.execute(__db_string)
            if __rawguild_settings == [] or __rawguild_settings is None:
                await db.execute(
                    "INSERT INTO GUILD_SETTINGS (guild_id) VALUES "
                    f"('{self.guild.id}')"
                )
                LOGGER.info(f"Added guild settings for {self.guild.name} ({self.guild.id}) to database.")
                __rawguild_settings = await db.execute(__db_string)
            
            self.ymca_green_book_announce_channel = None if __rawguild_settings[0][0] is None else self.guild.get_channel(int(__rawguild_settings[0][0]))
            self.music_channel = None if __rawguild_settings[0][1] is None else self.guild.get_channel(int(__rawguild_settings[0][1]))
    
    
    
    async def __update_database(self, __rawguild: list) -> None:
        update_params = []
        if self.guild.name != __rawguild[0][2]: update_params.append(f"name='{self.guild.name}'")
        if self.guild.owner_id != __rawguild[0][3]: update_params.append(f"owner_id='{self.guild.owner_id}'")
        if self.guild.member_count != __rawguild[0][4]: update_params.append(f"member_count='{self.guild.member_count}'")
        
        if update_params:
            await db.execute(
                f"UPDATE GUILDS SET {','.join(update_params)} WHERE guild_id='{self.guild.id}'"
            )
            LOGGER.debug(f"Updated guild {self.guild.name} ({self.guild.id}) in database.")
        
        
    
###########################################################################################################################
    
    
