'''
Debug testing file
'''

import random

from Database.MikoGuild import MikoGuild
from Database.MikoUser import MikoUser
from discord.ext import commands
from discord.ext.commands import Context

class Tester(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    # Simple magic 8-ball command
    @commands.command(name='8ball', aliases=['8b'])
    async def eightball(self, ctx: Context, *args):
        
        u = MikoMember(user=ctx.author, client=self.client)
        if (await u.profile).cmd_enabled('EIGHT_BALL') != 1: return
        await u.increment_statistic('EIGHT_BALL')

        user = ctx.message.author
        if len(args) == 0:
            await ctx.send(f'{user.mention} you need to enter a question!')
        else:
            responses = ['It is certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes - definitely.', 'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.']
            await ctx.send(f'{user.mention} {random.choice(responses)}')

async def setup(client: commands.Bot):
    await client.add_cog(Tester(client))