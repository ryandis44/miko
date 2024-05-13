'''
File for syncing app commands to the Discord API
'''


import discord
import typing

from Database.MikoCore import MikoCore
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()



class Slash(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client
    
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     self.tree = app_commands.CommandTree(self.client)

    # Sync command cannot be a slash command because you have to sync slash commands, so we cannot sync
    # the sync command if we have not synced slash commands. Sync sync sync
    @commands.command(name='sync', aliases=['sc'])
    @commands.guild_only()
    async def sync(
      self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: typing.Optional[typing.Literal["~", "*", "^", "G"]] = None) -> None:
        mc = MikoCore()
        await mc.user_ainit(user=ctx.author, client=self.client)
        if mc.user.bot_permission_level <= 4: return
        if spec is not None: await ctx.channel.send("Attempting to sync commands...")
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                try:
                    ctx.bot.tree.copy_global_to(guild=ctx.guild)
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                except Exception as e: print(e)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            elif spec == "G":
                synced = await ctx.bot.tree.sync()
            else:
                await ctx.channel.send(
                    "Please provide a modifier: `sc <modifier>`\n"+
                    "`~` Locally syncs private guild commands to current guild (if they are listed on this server)\n"+
                    "`*` Syncs global commands to current guild\n"+
                    "`^` Clears all locally synced commands from current guild\n"+
                    "`G` Globally syncs all non-private commands to all guilds\n"
                )
                return

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        # for guild in guilds:
        #     try:
        #         await ctx.bot.tree.sync(guild=guild)
        #     except discord.HTTPException:
        #         pass
        #     else:
        #         ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")



async def setup(client: commands.Bot):
    await client.add_cog(Slash(client))