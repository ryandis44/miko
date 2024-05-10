'''
Debug testing file
'''

import random

from Database.MikoCore import MikoCore
from discord.ext import commands
from discord.ext.commands import Context

class Tester(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    # Simple magic 8-ball command
    @commands.command(name='8ball', aliases=['8b'])
    async def magic_eightball(self, ctx: Context, *args):
        


    @commands.command(name='roleassignment', aliases=['ra'])
    @commands.guild_only()
    async def holiday(self, ctx: Context):
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.guild.profile_text != "THE_BOYS": return
        await mc.increment_statistic('EIGHT_BALL')
        
        await ctx.send(embed=get_holiday(ctx, "EMBED"))

async def setup(client: commands.Bot):
    await client.add_cog(Tester(client))