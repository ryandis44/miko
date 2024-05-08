'''
This class is responsible for handling all user data
'''



import discord
from Database.MikoGuild import MikoGuild
from Database.MySQL import AsyncDatabase
db = AsyncDatabase("Database.MikoUser.py")



class MikoUser(MikoGuild):
    
    def __init__(self, guild: discord.Guild, client: discord.Client) -> None:
        
        super().__init__(guild=guild, client=client)
        self.guild = guild
        self.client = client
        
        
        
    def __str__(self) -> str: return f"MikoGuild | {self.guild}"
        
        
        
    async def ainit(self, check_exists: bool = True) -> None:
        
        if check_exists:
            await self.__exists()
            await super().ainit()
    
    
    '''
    Insert guild into database if it does not exist, otherwise
    update the guild in the database
    '''
    async def __exists(self) -> None:
        __rawguild = await db.execute(
            f"SELECT * FROM GUILDS WHERE guild_id={self.guild.id}"
        )
        print(__rawguild)
        
        # if guild does not exist in database, insert it
        if __rawguild == [] or __rawguild is None:
            await db.execute(
                "INSERT INTO GUILDS (guild_id, name, owner_id, member_count) VALUES "
                f"('{self.guild.id}', '{self.guild.name}', '{self.guild.owner_id}', '{self.guild.member_count}')"
            )






###########################################################################################################################