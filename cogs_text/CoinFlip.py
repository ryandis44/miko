'''
Debug testing file
'''

import random

from Database.MikoCore import MikoCore
from discord.ext import commands
from discord.ext.commands import Context

class CoinFlip(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    # Simple coinflip command
    @commands.command(name='flip', aliases=['fl'])
    async def flip(self, ctx: Context):
        
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.profile.cmd_enabled('COIN_FLIP') == 0: return
        elif mc.profile.cmd_enabled('COIN_FLIP') == 2:
            await ctx.send(mc.tunables('COMMAND_DISABLED_MESSAGE'), silent=True)
            return
        await mc.user.increment_statistic('COIN_FLIP')
        
        user = ctx.message.author
        coin = ['Heads', 'Tails']
        await ctx.send(f'{user.mention} {random.choice(coin)}!')

async def setup(client: commands.Bot):
    await client.add_cog(CoinFlip(client))