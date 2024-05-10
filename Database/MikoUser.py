'''
This class is responsible for handling all user data
'''



import discord
import logging
import time

from Database.MikoGuild import MikoGuild
from Database.MySQL import AsyncDatabase
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoUser(MikoGuild):
    
    def __init__(self, user: discord.User|discord.Member, client: discord.Client) -> None:
        self.user = user
        self.client = client
        
        self.bot_permission_level: int = 0
        self.last_interaction: int = 0
        
        
        
    def __str__(self) -> str: return f"MikoUser | {self.user.name}"
        
        
        
    async def ainit(self, check_exists: bool = True) -> None:
        if check_exists: await self.__exists() # Member MUST be initialized first, due to the foreign key constraint on GUILDS.owner_id
    
    
    
    '''
    Insert user into database if it does not exist, otherwise
    update the user in the database
    '''
    async def __exists(self) -> None:
        __rawuser = await db.execute(
            f"SELECT perm_level,last_interaction FROM USERS WHERE user_id='{self.user.id}'"
        )
        
        # if user does not exist in database, insert it
        if __rawuser == () or __rawuser is None:
            self.bot_permission_level = 1
            self.last_interaction = int(time.time())
            await db.execute(
                "INSERT INTO USERS (user_id, username, is_bot, last_interaction) VALUES "
                f"('{self.user.id}', '{self.user.name}', '{str(1) if self.user.bot else str(0)}', '{self.last_interaction}')"
            )
            LOGGER.info(f"Added user {self.user.name} ({self.user.id}) to database.")
            
        else:
            self.bot_permission_level = __rawuser[0][0]
            self.last_interaction = __rawuser[0][1]

        if self.is_member:
            print("MikoUser is a member")
            super().__init__(guild=self.user.guild, client=self.client)
            await super().ainit()



###########################################################################################################################



    @property
    def is_member(self) -> bool: return isinstance(self.user, discord.Member)