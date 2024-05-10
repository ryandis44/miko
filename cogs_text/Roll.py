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
        if mc.profile.cmd_enabled('ROLL') != 1:
            await ctx.send(f"You do not have permission to use this command")
            return
        
        user = ctx.message.author
        roll = random.randint(0, 100)
        if roll < 10:
            if roll == 1:
                await ctx.send(f'{user.mention} rolled a **{roll}**! ...better than zero')
            elif roll == 7:
                await ctx.send(f'{user.mention} rolled a **{roll}**! Looks like lucky number seven isn\'t so lucky this time...')
            else:
                await ctx.send(f'{user.mention} rolled a **{roll}**! My my, quite unfortunate! <:okand:947697439048073276>')
        
        elif roll > 90:
            if roll == 100:
                await ctx.send(f'{user.mention} rolled a **:100:**! GG. Might as well just give <@221438665749037056> the card.')
            else:
                await ctx.send(f'{user.mention} rolled a **{roll}**! Very impressive! <@357939301100683276> <:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368><:hector_talking:947690384841146368>')
        
        elif roll == 50:
            await ctx.send(f'{user.mention} rolled a **{roll}**! It could go either way at this point!')
        elif roll == 69:
            await ctx.send(f'{user.mention} rolled a **{roll}**! :smirk:')
        else:
            await ctx.send(f'{user.mention} rolled a **{roll}**!')

async def setup(client: commands.Bot):
    await client.add_cog(Roll(client))