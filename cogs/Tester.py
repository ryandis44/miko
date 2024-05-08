'''
Debug testing file
'''

import random

from Database.MikoGuild import MikoGuild
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
        
        g = MikoGuild(guild=ctx.guild, client=self.client)
        await g.ainit()
        
        await ctx.send(
            f"{g}"
        )

async def setup(client: commands.Bot):
    await client.add_cog(Tester(client))