'''
Debug testing file
'''



from Database.MikoCore import MikoCore
from discord.ext import commands
from discord.ext.commands import Context

class Tester(commands.Cog):
    def __init__(self, client: commands.Bot): self.client = client

    @commands.command(name='test', aliases=['t'])
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
        if mc.user.bot_permission_level <= 4: return
        await mc.user.increment_statistic('TESTER_CMD')
        
        await ctx.send(
            f"{mc} // {mc.user} // Miko Permission level: {mc.user.bot_permission_level}\n"
            f"{mc.guild} // {mc.profile}\n"
            f"{mc.user.username} // <t:{mc.user.last_interaction}:R>\n"
            f"{mc.user.usernames}\n"
        )

async def setup(client: commands.Bot):
    await client.add_cog(Tester(client))