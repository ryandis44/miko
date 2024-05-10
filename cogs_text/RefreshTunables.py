'''
Debug testing file
'''

import random

from Database.MikoCore import MikoCore
from Database.tunables import tunables_refresh
from discord.ext import commands
from discord.ext.commands import Context

class RefreshTunables(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    @commands.command(name='refreshtunables', aliases=['rt'])
    @commands.guild_only()
    async def refreshtunables(self, ctx: Context):
        
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.user.bot_permission_level <= 4: return
        
        await ctx.send(f"Refreshing tunables...")
        await tunables_refresh()
        await ctx.send(f"Tunables refreshed!")

async def setup(client: commands.Bot):
    await client.add_cog(RefreshTunables(client))