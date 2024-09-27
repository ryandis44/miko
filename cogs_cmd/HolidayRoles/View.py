'''
Fix button for holiday roles (bc im lazy)
'''

import asyncio
import discord

from cogs_cmd.HolidayRoles.holiday_roles import get_holiday
from Database.MikoCore import MikoCore



class UnfuckHolidayRoles(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, mc: MikoCore) -> None:
        super().__init__(timeout=mc.tunables('GLOBAL_VIEW_TIMEOUT'))
        self.interaction = interaction
        self.mc = mc
        self.clear_items()
        self.add_item(UnfuckButton(mc))
    
    
    async def on_timeout(self) -> None:
        try:
            _msg = await self.interaction.original_response()
            await _msg.edit(
                content=self.mc.tunables('GLOBAL_VIEW_TIMEOUT_MESSAGE')
            )
        except: pass
    
    
    
    async def interaction_check(self, interaction: discord.Interaction) -> None:
        return interaction.user.id == interaction.guild.owner.id



class UnfuckButton(discord.ui.Button):
    def __init__(self, mc: MikoCore) -> None:
        super().__init__(
            label="Unfuck",
            style=discord.ButtonStyle.primary
        )
        self.mc = mc
    
    
    
    async def callback(self, interaction: discord.Interaction) -> None:
        
        # Remove all holiday roles from members with multiple roles
        for member in get_holiday(interaction=interaction, mc=self.mc, info_to_return="MULTIPLE"):
            member: discord.Member
            await member.remove_roles(*get_holiday(interaction=interaction, mc=self.mc, info_to_return="ALL_ROLES"), reason="Unfucking holiday roles")
            await asyncio.sleep(1)
        
        # Add holiday role to unassigned users
        for member in get_holiday(interaction=interaction, mc=self.mc, info_to_return="UNASSIGNED"):
            member: discord.Member
            _role = get_holiday(interaction=interaction, mc=self.mc, info_to_return="ROLE")
            _role = interaction.guild.get_role(_role)
            await member.add_roles(_role, reason="Unfucking holiday roles")
            await asyncio.sleep(1)
        
        await interaction.response.edit_message(
            content=(
                "# Unfucked holiday roles"
            )
        )