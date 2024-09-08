'''
This class is responsible for handling all user data
'''



import asyncio
import discord
import logging
import time

from cogs_cmd.HolidayRoles.holiday_roles import get_holiday
from Database.MikoGuild import MikoGuild
from Database.MikoMessage import MikoMessage
from Database.MikoTextChannel import MikoTextChannel
from Database.MikoUser import MikoUser
from Database.MySQL import AsyncDatabase
from Database.tunables import tunables, PermissionProfile
from discord.ext.commands import Bot
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()

USER_LOCKS = {}

# Temporary lock, will replace with redis implementation soon
async def presence_lock(user: discord.Member) -> asyncio.Lock:
    val = USER_LOCKS.get(user.id)
    
    if val is None:
        lock = asyncio.Lock()
        USER_LOCKS[user.id] = {
            'at': int(time.time()),
            'lock': lock
        }
        return lock
    
    val['at'] = int(time.time())
    return val['lock']

class MikoCore:
    
    def __init__(self) -> None:
        self.user = MikoUser()
        self.guild = MikoGuild()
        self.channel = MikoTextChannel()
        self.message = MikoMessage()
        
        self.threads = [discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.news_thread]
        
        
        
    def __str__(self) -> str: return f"MikoCore Object"
    
    
    
    '''
    Logic below:
    - Initialize MikoUser
    - If the user is a member, initialize MikoGuild
    '''
    async def user_ainit(self, user: discord.User|discord.Member, client: Bot, check_exists: bool = True) -> None:
        async with await presence_lock(user):
            await self.user.ainit(user=user, client=client, check_exists=check_exists)
            if self.user.is_member: self.guild: MikoGuild = self.user.guild
            if self.user.new_user:
                await self.__role_assign()
                await self.__greet_new_members()
    
    
    
    async def guild_ainit(self, guild: discord.Guild, client: Bot, check_exists: bool = True) -> None:
        await self.guild.ainit(guild=guild, client=client, check_exists=check_exists)
        
    
    
    async def channel_ainit(self, channel: discord.TextChannel|discord.Thread, client: Bot, check_exists: bool = True) -> None:
        await self.channel.ainit(channel=channel, client=client, check_exists=check_exists)
    
    
    
    '''
    Logic below:
    - Initialize MikoMessage
    - Initialize MikoUser (and MikoGuild, handled in user_ainit, if user is also a member)
    - Initialize MikoTextChannel (if user is a member)
    '''
    async def message_ainit(self, message: discord.Message, client: Bot) -> None:
        await self.message.ainit(message=message, client=client)
        await self.user_ainit(user=message.author, client=client)
        if self.user.is_member: await self.channel_ainit(channel=message.channel, client=client)
    
    
    
###########################################################################################################################    
    
    
    
    # To reduce imports from multiple files, this function is used to access
    # tunables in files that already access MikoCore
    def tunables(self, key: str) -> str: return tunables(key)
    
    
    
    # Responsible for enforcing whether a feature/command is enabled globally,
    # or for a specific guild. If no guild is detected, the default 'ACTIVE'
    # profile is used
    @property
    def profile(self) -> PermissionProfile:
        __profile: PermissionProfile = self.tunables(f'PERMS_PROFILE_{self.guild.profile_text}')
        if __profile is not None:
            __profile.inject_guild(self.guild.guild_settings)
            return __profile
        else:
            LOGGER.warning(f"Guild profile '{self.guild.profile_text}' for guild {self.guild.guild.name} ({self.guild.guild.id}) not found. Using default 'ACTIVE' profile")
            return self.tunables('PERMS_PROFILE_ACTIVE')
    
    
    
    async def __role_assign(self) -> None:
        if self.profile.feature_enabled('ROLE_ASSIGN') != 1 or self.guild.role_assign is None: return
        
        try: await self.user.user.add_roles(self.guild.role_assign, reason="Member Join Role enabled. /settings to disable")
        except Exception as e:
            LOGGER.error(f'Failed to assign joining role to user {self.user.user} in guild {self.guild.guild}, removing role from DB | {e}')
            await self.guild.set_role_assign(role_id=None)
        
        
        try: 
            # The boys server custom implementation
            if self.guild.profile_text != "THEBOYS": return
            
            holiday_role = self.guild.guild.get_role(get_holiday(self.user.user, "ROLE", self))
            await self.user.user.add_roles(holiday_role, reason="The Boys Hangout custom implementation")
            
            if self.user.user.bot:
                bot = self.guild.guild.get_role(890642126445084702)
                await self.user.user.add_roles(bot, reason="The Boys Hangout custom implementation")
        except Exception as e:
            LOGGER.error(f'Failed to run the boys server role implementation | {e}')
    
    
    
    async def __greet_new_members(self) -> None:
        if self.profile.feature_enabled('GREET_NEW_MEMBERS') != 1: return
        
        try:
            channel = self.guild.guild.system_channel
            if channel is None or not channel.permissions_for(self.guild.guild.me).send_messages: return
            
            await asyncio.sleep(1) # ensure welcome message is sent after (discord) system join message
            
            new = self.user.first_join == self.user.latest_join
            
            await channel.send(
                f'Hi {self.user.user.mention}, welcome{" BACK " if not new else " "}to {self.guild.guild.name}! :tada:\n'
                f'> You are unique member `#{self.user.member_number}`', silent=True
            )
        except Exception as e:
            LOGGER.error(f'Failed to greet new member {self.user.user} in guild {self.guild.guild} | {e}')



    def ai_remove_mention(self, msg: list) -> list:
        for i, word in enumerate(msg):
            if word in [f"<@{str(self.mc.channel.client.user.id)}>"]:
                # Remove word mentioning Miko
                msg.pop(i)
        return msg



    async def ai_check_attachments(self, message: discord.Message|CachedMessage) -> str|None:
        if len(message.attachments) == 0: return None
        if message.attachments[0].filename != "message.txt": return None
        try: return (await message.attachments[0].read()).decode()
        except:
            try: return message.attachments[0].data
            except: return None