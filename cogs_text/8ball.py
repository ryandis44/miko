'''
Debug testing file
'''

import random

from Database.MikoCore import MikoCore
from discord.ext import commands
from discord.ext.commands import Context

class EightBall(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    # Simple magic 8-ball command
    @commands.command(name='8ball', aliases=['8b'])
    async def magic_eightball(self, ctx: Context, *args):
        
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.profile.cmd_enabled('EIGHT_BALL') == 0: return
        elif mc.profile.cmd_enabled('EIGHT_BALL') == 2:
            await ctx.send(mc.tunables('COMMAND_DISABLED_MESSAGE'), silent=True)
            return
        await mc.increment_statistic('EIGHT_BALL')

        user = ctx.message.author
        if len(args) == 0:
            await ctx.send(f'{user.mention} you need to enter a question!')
        else:
            responses = ['It is certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes - definitely.', 'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.']
            await ctx.send(f'{user.mention} {random.choice(responses)}')

async def setup(client: commands.Bot):
    await client.add_cog(EightBall(client))