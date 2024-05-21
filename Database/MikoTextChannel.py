'''
This class is responsible for handling all user data
'''



import discord
import logging

from Database.MySQL import AsyncDatabase
from discord.ext.commands import Bot
from misc.misc import sanitize_name
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoTextChannel:
    
    def __init__(self) -> None:
        self.channel: discord.TextChannel = None
    
    
    
    async def ainit(self, channel: discord.TextChannel, client: Bot, check_exists: bool = True) -> None:
        self.channel = channel
        self.client = client
        if check_exists: await self.__exists()
    
    
    
    async def __exists(self) -> None:
        __rawchannel = await db.execute(
            f"SELECT name,channel_id "
            f"FROM TEXT_CHANNELS WHERE channel_id='{self.channel.id}'"
        )
        
        if __rawchannel == [] or __rawchannel is None:
            await db.execute(
                "INSERT INTO TEXT_CHANNELS (guild_id, channel_id, name) VALUES "
                f"('{self.channel.guild.id}', '{self.channel.id}', '{sanitize_name(self.channel.name)}')"
            )
            LOGGER.info(f"Added {self.channel.name} in guild {self.channel.guild} to database")
        
        else: await self.__update_database(__rawchannel)
        
        __db_string = (
            "SELECT text_ai_mode,text_ai_threads "
            f"FROM CHANNEL_SETTINGS WHERE channel_id='{self.channel.id}'"
        )
        __rawchannel_settings = await db.execute(__db_string)
        if __rawchannel_settings == [] or __rawchannel_settings is None:
            await db.execute(
                "INSERT INTO CHANNEL_SETTINGS (channel_id) VALUES "
                f"('{self.channel.id}')"
            )
            LOGGER.info(f"Added {self.channel.name} settings in guild {self.channel.guild} to database")
            __rawchannel_settings = await db.execute(__db_string)
        
        self.text_ai_mode = __rawchannel_settings[0][0]
        self.text_ai_threads = __rawchannel_settings[0][1]
    
    
    
    async def __update_database(self, __rawchannel: list) -> None:
        update_params = []
        if sanitize_name(self.channel.name) != __rawchannel[0][0]: update_params.append(f"name='{sanitize_name(self.channel.name)}'")
        
        if update_params:
            await db.execute(
                f"UPDATE TEXT_CHANNELS SET {', '.join(update_params)} WHERE channel_id='{self.channel.id}'"
            )
            LOGGER.debug(f"Updated {self.channel.name} in guild {self.channel.guild} in database")



###########################################################################################################################



    @property
    def channel_settings(self) -> dict:
        return {
            'text_ai_mode': self.text_ai_mode,
            'text_ai_threads': self.text_ai_threads
        }