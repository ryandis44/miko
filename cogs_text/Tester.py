'''
Debug testing file
'''

import random

from Database.MikoCore import MikoCore
from Database.MikoGuild import MikoGuild
from Database.MikoUser import MikoUser
from discord.ext import commands
from discord.ext.commands import Context

class Tester(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    @commands.command(name='test', aliases=['t'])
    @commands.guild_only()
    async def tester(self, ctx: Context):
        
        # u = MikoMember(user=ctx.author, client=self.client)
        # if (await u.profile).cmd_enabled('ROLL') != 1: return
        # await u.increment_statistic('ROLL')
        
        # g = MikoGuild(guild=ctx.guild, client=self.client)
        # await g.ainit()
        
        # u = MikoUser(user=ctx.author, client=self.client)
        # await u.ainit()
        
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        await mc.guild_ainit(guild=ctx.guild, client=self.client)
        
        await ctx.send(
            f"{mc} // {mc.user}\n"
            f"{mc.profile}\n"
            f"{mc.guild}"
        )

async def setup(client: commands.Bot):
    await client.add_cog(Tester(client))