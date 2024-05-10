'''
Legacy Text Command

File for 'mroll, mr' command
'''

import random

from Database.MikoCore import MikoCore
from discord.ext import commands
from discord.ext.commands import Context

class Roll(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    # Generates a random number between 0 and 100 [inclusive]
    @commands.command(name='roll', aliases=['r'])
    async def roll(self, ctx: Context):
        
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.profile.cmd_enabled('ROLL') == 0: return
        elif mc.profile.cmd_enabled('ROLL') == 2:
            await ctx.send(mc.tunables('COMMAND_DISABLED_MESSAGE'), silent=True)
            return
        await mc.increment_statistic('ROLL')
        
        user = ctx.message.author
        roll = random.randint(0, 100)
        if roll < 10:
            if roll == 1:
                await ctx.send(f'{user.mention} rolled a **{roll}**! ...better than zero', silent=True)
            elif roll == 7:
                await ctx.send(f'{user.mention} rolled a **{roll}**! Looks like lucky number seven isn\'t so lucky this time...', silent=True)
            else:
                await ctx.send(f'{user.mention} rolled a **{roll}**! My my, quite unfortunate! <:okand:947697439048073276>', silent=True)
        
        elif roll > 90:
            if roll == 100:
                await ctx.send(f'{user.mention} rolled a **:100:**! GG. Might as well just give <@221438665749037056> the card.', silent=True)
            else:
                await ctx.send(f'{user.mention} rolled a **{roll}**! Very impressive! <@357939301100683276> <:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368>', silent=True)
        
        elif roll == 50:
            await ctx.send(f'{user.mention} rolled a **{roll}**! It could go either way at this point!', silent=True)
        elif roll == 69:
            await ctx.send(f'{user.mention} rolled a **{roll}**! :smirk:', silent=True)
        else:
            await ctx.send(f'{user.mention} rolled a **{roll}**!', silent=True)

async def setup(client: commands.Bot):
    await client.add_cog(Roll(client))