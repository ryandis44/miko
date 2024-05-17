'''
This class is responsible for handling all guild data
'''



import discord
import logging

from Database.MySQL import AsyncDatabase
from discord.ext.commands import Bot
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoMessage:
    
    def __init__(self) -> None:
        self.message: discord.Message = None
        self.client: Bot = None
    
    
    
    def __str__(self) -> str: return f"MikoMessage | {self.message.author.name}"
    
    
    
    async def ainit(self, message: discord.Message, client: Bot) -> None:
        self.message = message
        self.client = client