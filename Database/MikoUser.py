'''
This class is responsible for handling all user data
'''



import discord
import logging
import time

from Database.MikoGuild import MikoGuild
from Database.MySQL import AsyncDatabase
from discord.ext.commands import Bot
from misc.misc import sanitize_name
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()



class MikoUser:
    
    def __init__(self) -> None:
        self.guild = MikoGuild()
        self.user: discord.User|discord.Member = None
        self.client: Bot = None
        
        self.bot_permission_level: int = 0
        self.last_interaction: int = 0
        self.usernames: list = []
        
        self.new_user: bool = False
        
        
        
    def __str__(self) -> str: return f"MikoUser | {self.user.name}"
        
        
        
    async def ainit(self, user: discord.User|discord.Member, client: Bot, check_exists: bool = True) -> None:
        self.user = user
        self.client = client
        if check_exists: await self.__exists() # Member MUST be initialized first, due to the foreign key constraint on GUILDS.owner_id
    
    
    
    '''
    Insert user into database if it does not exist, otherwise
    update the user in the database
    '''
    async def __exists(self) -> None:
        
        # User table processing
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
                f"('{self.user.id}', '{sanitize_name(self.user.name)}', '{str(1) if self.user.bot else str(0)}', '{self.last_interaction}')"
            )
            LOGGER.info(f"Added user {self.user.name} ({self.user.id}) to database.")
            self.new_user = True
            
        else:
            self.bot_permission_level: int = __rawuser[0][0]
            self.usernames: list = await self.__get_usernames()
            
            await self.__update_database(__rawuser)

        ################################################################################################################

        # Guild member table processing
        if self.is_member:
            await self.guild.ainit(guild=self.user.guild, client=self.client)
            
            __guild_member_str = (
                "SELECT first_join, latest_join "
                f"FROM GUILD_MEMBERS WHERE user_id='{self.user.id}' AND guild_id='{self.guild.guild.id}'"
            )
            
            __guild_member = await db.execute(__guild_member_str)
            
            if __guild_member == [] or __guild_member is None:
                await db.execute(
                    "INSERT INTO GUILD_MEMBERS (user_id, guild_id, first_join, latest_join) VALUES "
                    f"('{self.user.id}', '{self.guild.guild.id}', '{int(self.user.joined_at.timestamp())}', '{int(self.user.joined_at.timestamp())}')"
                )
                LOGGER.info(f"Added user {self.user.name} ({self.user.id}) to guild members for guild {self.guild.guild.name} ({self.guild.guild.id}) in database.")
                __guild_member = await db.execute(__guild_member_str)
                self.new_user = True
            
            elif int(self.user.joined_at.timestamp()) != __guild_member[0][1]:
                await db.execute(
                    f"UPDATE GUILD_MEMBERS SET latest_join='{int(self.user.joined_at.timestamp())}' "
                    f"WHERE user_id='{self.user.id}' AND guild_id='{self.guild.guild.id}'"
                )
                self.new_user = True
            
            self.first_join = __guild_member[0][0]
            self.latest_join = int(self.user.joined_at.timestamp())
            
            # Obtain generated user metadata
            __guild_member_meta_str = (
                "SELECT member_number,user_id "
                f"FROM GENERATED_USER_META WHERE user_id='{self.user.id}' AND guild_id='{self.guild.guild.id}'"
            )
            __guild_member_meta = await db.execute(__guild_member_meta_str)
            
            if __guild_member_meta is None or __guild_member_meta == []:
                __num = await db.execute(
                    "SELECT member_number FROM GENERATED_USER_META WHERE "
                    f"guild_id='{self.guild.guild.id}' ORDER BY member_number DESC LIMIT 1"
                )
                await db.execute(
                    "INSERT INTO GENERATED_USER_META (member_number, user_id, guild_id) VALUES "
                    f"('{__num + 1}', '{self.user.id}', '{self.guild.guild.id}')"
                )
                __guild_member_meta = await db.execute(__guild_member_meta_str)
                self.new_user = True
            
            
            self.member_number = __guild_member_meta[0][0] if __guild_member_meta != [] else None
            
        ################################################################################################################
        
        # User settings table processing
        __db_string = (
            "SELECT big_emojis,track_playtime,track_voicetime "
            f"FROM USER_SETTINGS WHERE user_id='{self.user.id}'"
        )
        __rawuser_settings = await db.execute(__db_string)
        if __rawuser_settings == [] or __rawuser_settings is None:
            await db.execute(
                "INSERT INTO USER_SETTINGS (user_id) VALUES "
                f"('{self.user.id}')"
            )
            LOGGER.info(f"Added user settings for {self.user.name} ({self.user.id}) to database.")
            __rawuser_settings = await db.execute(__db_string)
        
        self.__do_big_emojis = True if __rawuser_settings[0][0] == "TRUE" else False
        self.do_track_playtime = True if __rawuser_settings[0][1] == "TRUE" else False
        self.do_track_voicetime = True if __rawuser_settings[0][2] == "TRUE" else False



    # Updates the user's information in the database, if it has changed
    async def __update_database(self, __rawuser: list) -> None:
        update_params = []
        update_params.append("UPDATE USERS SET ")
        
        self.last_interaction = int(time.time())
        if self.last_interaction != __rawuser[0][1]:
            update_params.append(f"last_interaction='{self.last_interaction}'")
        
        self.username = sanitize_name(self.user.name)
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
    def user_settings(self) -> dict:
        return {
            'big_emojis': self.do_big_emojis,
            'track_playtime': self.do_track_playtime,
            'track_voicetime': self.do_track_voicetime
        }
    
    
    
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
    
    
    
    @property
    def miko_avatar(self) -> discord.Asset:
        if not self.is_member: return self.user.avatar
        if self.user.guild_avatar is None: return self.user.avatar
        elif self.guild.do_nickname_in_ctx: return self.user.guild_avatar
        return self.user.avatar
    
    
    
    @property
    def manage_guild(self) -> bool:
        if not self.is_member: return False
        perms = self.user.guild_permissions
        if perms.administrator: return True
        if perms.manage_guild: return True
        if self.bot_permission_level >= 5: return True
        return False
    
    
    
    def manage_channel(self, channel: discord.TextChannel) -> bool:
        if not self.is_member: return False
        manage_channels = channel.permissions_for(self.user).manage_channels
        if manage_channels: return True
        if self.bot_permission_level >= 5: return True
        return False
    
    
    
    # Guild big emoji enforcement
    @property
    def do_big_emojis(self) -> bool:
        if not self.is_member: return self.__do_big_emojis
        return self.__do_big_emojis if self.guild.do_big_emojis else False