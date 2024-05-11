'''
File for the GreenBook command
'''



import os
import discord

from Database.MikoCore import MikoCore
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from YMCA.GreenBook.UI import BookView
load_dotenv()

class BookCog(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client
    
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     self.tree = app_commands.CommandTree(self.client)


    @app_commands.command(name="book", description=f"{os.getenv('APP_CMD_PREFIX')}View/Edit the Book [YMCA Servers Only]")
    @app_commands.guild_only
    async def book(self, interaction: discord.Interaction):
        await BookView(original_interaction=interaction).ainit()


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.client)
        if await mc.profile.cmd_enabled('YMCA_GREEN_BOOK') == 0:
            await interaction.response.send_message(content=mc.tunables('COMMAND_DISABLED_GUILD_MESSAGE'), ephemeral=True)
            return False
        elif await mc.profile.cmd_enabled('YMCA_GREEN_BOOK') == 2:
            await interaction.response.send_message(content=mc.tunables('COMMAND_DISABLED_MESSAGE'), ephemeral=True)
            return False

        await interaction.response.send_message(content=f"{mc.tunables('LOADING_EMOJI')}", ephemeral=True)
        await mc.user.increment_statistic('YMCA_GREEN_BOOK_OPENED')
        return True



async def setup(client: commands.Bot):
    await client.add_cog(BookCog(client))