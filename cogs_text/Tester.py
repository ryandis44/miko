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
        
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.user.bot_permission_level <= 4: return
        await mc.user.increment_statistic('TESTER_CMD')
        
        await ctx.send(
            f"{mc} // {mc.user} // Miko Permission level: {mc.user.bot_permission_level}\n"
            f"{mc.guild} // {mc.profile}\n"
            f"{mc.user.username} // <t:{mc.user.last_interaction}:R>\n"
            f"{mc.user.usernames}\n"
            f"{mc.user.do_big_emojis} // {mc.guild.do_greet_new_members} // {mc.user.do_track_playtime}\n"
            f"{mc.profile.feature_enabled('BIG_EMOJIS')}"
            f"{mc.user.client.guilds}"
        )

async def setup(client: commands.Bot):
    await client.add_cog(Tester(client))