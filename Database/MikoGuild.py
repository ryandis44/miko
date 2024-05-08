'''
This class is responsible for handling all guild data
'''



import discord
from Database.MySQL import AsyncDatabase
db = AsyncDatabase("Database.MikiGuild.py")



class MikoGuild:
    
    def __init__(self, guild: discord.Guild, client: discord.Client) -> None:
        
        self.guild = guild
        self.client = client
        
        
        
    def __str__(self) -> str: return f"MikoGuild | {self.guild}"
        
        
        
    async def ainit(self, check_exists: bool = True) -> None:
        
        if check_exists: await self.__exists()
    
    
    
    async def __exists(self) -> None:
        __rawguild = await db.execute(
            f"SELECT * FROM GUILDS WHERE guild_id={self.guild.id}"
        )
        print(__rawguild)
        
        if __rawguild == [] or __rawguild is None:
            print("executing")
            await db.execute(
                "INSERT INTO GUILDS (guild_id, name, owner_id, member_count) VALUES "
                f"('{self.guild.id}', '{self.guild.name}', '{self.guild.owner_id}', '{self.guild.member_count}')"
            )

        