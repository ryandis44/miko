import os
import discord
from Database.tunables import *
from discord.ext import commands
from discord import app_commands
from Database.GuildObjects import MikoMember
from YMCA.GreenBook.UI import BookView
from dotenv import load_dotenv
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
        u = MikoMember(user=interaction.user, client=interaction.client)
        await u.ainit()
        if (await u.profile).cmd_enabled('GREEN_BOOK') == 0:
            await interaction.response.send_message(content=tunables('COMMAND_DISABLED_GUILD'), ephemeral=True)
            return False
        elif (await u.profile).cmd_enabled('GREEN_BOOK') == 2:
            await interaction.response.send_message(content=tunables('COMMAND_DISABLED_TUNABLES'), ephemeral=True)
            return False

        await interaction.response.send_message(content=f"{tunables('LOADING_EMOJI')}", ephemeral=True)
        await u.increment_statistic('YMCA_GREEN_BOOK_OPENED')
        return True



async def setup(client: commands.Bot):
    await client.add_cog(BookCog(client))