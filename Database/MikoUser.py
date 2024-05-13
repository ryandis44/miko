'''
This class is responsible for handling all user data
'''



import discord
import logging
import time

from Database.MikoGuild import MikoGuild
from Database.MySQL import AsyncDatabase
from misc.misc import sanitize_name
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoUser:
    
    def __init__(self) -> None:
        self.guild = MikoGuild()
        self.user: discord.User|discord.Member = None
        self.client: discord.Client = None
        
        self.bot_permission_level: int = 0
        self.last_interaction: int = 0
        self.usernames: list = []
        
        
        
    def __str__(self) -> str: return f"MikoUser | {self.user.name}"
        
        
        
    async def ainit(self, user: discord.User|discord.Member, client: discord.Client, check_exists: bool = True) -> None:
        self.user = user
        self.client = client
        if check_exists: await self.__exists() # Member MUST be initialized first, due to the foreign key constraint on GUILDS.owner_id
    
    
    
    '''
    Insert user into database if it does not exist, otherwise
    update the user in the database
    '''
    async def __exists(self) -> None:
        __rawuser = await db.execute(
            f"SELECT perm_level,last_interaction,username "
            f"FROM USERS WHERE user_id='{self.user.id}'"
        )
        
        # if user does not exist in database, insert it
        if __rawuser == [] or __rawuser is None:
            self.bot_permission_level = 1
            self.last_interaction = int(time.time())
            await db.execute(
                "INSERT INTO USERS (user_id, username, is_bot, last_interaction) VALUES "
                f"('{self.user.id}', '{self.user.name}', '{str(1) if self.user.bot else str(0)}', '{self.last_interaction}')"
            )
            LOGGER.info(f"Added user {self.user.name} ({self.user.id}) to database.")
            
        else:
            self.bot_permission_level: int = __rawuser[0][0]
            self.usernames: list = await self.__get_usernames()
            
            await self.__update_database(__rawuser)

        if self.is_member: await self.guild.ainit(guild=self.user.guild, client=self.client)



    # Updates the user's information in the database, if it has changed
    async def __update_database(self, __rawuser: list) -> None:
        update_params = []
        update_params.append("UPDATE USERS SET ")
        
        self.last_interaction = int(time.time())
        if self.last_interaction != __rawuser[0][1]:
            update_params.append(f"last_interaction='{self.last_interaction}'")
        
        self.username = self.user.name
        if self.username != __rawuser[0][2]:
            update_params.append(
                f"{', 'if len(update_params) > 1 else ''}username='{self.username}'"
            )
            await self.__set_username_history(old_username=__rawuser[0][2])
        
        if len(update_params) > 1:
            update_params.append(f" WHERE user_id='{self.user.id}'")
            await db.execute(''.join(update_params))
        
        LOGGER.debug(f"Updated user {self.user.name} ({self.user.id}) in database.")



    async def __set_username_history(self, old_username: str) -> None:
        num_names = len(self.usernames)
        
        # Loop here to insert the user's current username into the database
        # if it is not already in the database history. For example, a user
        # changes their name for the first time, the old name is not in the
        # database history, so we insert it here and insert the new username
        # and when it was changed. If the user changes their name again, we
        # only insert the new name and when it was changed
        for i in [0,1]:
            if num_names != 0 and i > 0: break
            await db.execute(
                "INSERT INTO USERNAME_HISTORY (user_id, username, last_change) VALUES "
                f"('{self.user.id}', "
                f"'{sanitize_name((old_username)) if num_names+i == 0 and i == 0 else sanitize_name(self.user.name)}', "
                f"'{int(self.user.created_at.timestamp()) if num_names+i == 0 and i == 0 else self.last_interaction}')"
            )
    
    
    
    async def __get_usernames(self) -> list:
        __rawusernames = await db.execute(
            f"SELECT username,last_change FROM USERNAME_HISTORY WHERE user_id='{self.user.id}'"
        )
        names = []
        for item in __rawusernames:
            names.append(item[0])
            names.append(item[1])
        return names



###########################################################################################################################



    @property
    def is_member(self) -> bool: return isinstance(self.user, discord.Member)



    async def increment_statistic(self, key: str) -> None:
        val = await db.execute(
            f"SELECT count FROM USER_STATISTICS WHERE stat='{key}' AND user_id='{self.user.id}'"
        )
        if val == [] or val is None:
            await db.execute(
                "INSERT INTO USER_STATISTICS (stat, count, user_id) VALUES "
                f"('{key}', '{1}', '{self.user.id}')"
            )
        else:
            await db.execute(
                f"UPDATE USER_STATISTICS SET count=count+1 WHERE stat='{key}' AND user_id='{self.user.id}'"
            )