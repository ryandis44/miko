'''
Legacy text command migrated to application command

Holiday role command. Prints out a list of member count for each holiday role
and shows members with multiple roles. Also shows members that do not have
a holiday role assigned
'''



import discord
import logging
import os

from cogs_cmd.HolidayRoles.holiday_roles import get_holiday
from Database.MikoCore import MikoCore
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
load_dotenv()
LOGGER = logging.getLogger()

class HolidayRoles(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client
        
        
        
    group = app_commands.Group(name="holiday", description="Poll Commands")



    @group.command(name="roles", description=f"{os.getenv('APP_CMD_PREFIX')}Show holiday role embed")
    @app_commands.guild_only
    async def holiday(self, interaction: discord.Interaction):
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=self.client)
        if mc.profile.cmd_enabled('ROLE_ASSIGNMENT') == 0:
            await interaction.response.send_message(content=mc.tunables('COMMAND_DISABLED_GUILD_MESSAGE'), ephemeral=True)
            return
        elif mc.profile.cmd_enabled('ROLE_ASSIGNMENT') == 2:
            await interaction.response.send_message(content=mc.tunables('COMMAND_DISABLED_MESSAGE'), ephemeral=True)
            return

        await interaction.response.send_message(content=f"{mc.tunables('LOADING_EMOJI')}", ephemeral=True)
        await mc.user.increment_statistic('COMMAND_USED_ROLE_ASSIGNMENT')
        
        await interaction.edit_original_response(
            content=None,
            embed=get_holiday(interaction, "EMBED")
        )



async def setup(client: commands.Bot):
    await client.add_cog(HolidayRoles(client))