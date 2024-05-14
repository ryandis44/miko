'''
This class is responsible for handling all guild data
'''



import discord
import logging

from Database.MySQL import AsyncDatabase
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoMessage:
    
    def __init__(self) -> None:
        self.message: discord.Message = None
        self.client: discord.Client = None
    
    
    
    async def ainit(self, message: discord.Message, client: discord.Client) -> None:
        self.message = message
        self.client = client