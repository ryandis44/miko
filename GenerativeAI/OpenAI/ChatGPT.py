'''
Main file for all OpenAI textual API interactions
'''



import asyncio
import discord

from Database.MikoCore import MikoCore
from Database.tunables import tunables
from openai import OpenAI

openai_client = OpenAI(api_key=tunables('OPENAI_API_KEY'))

class RegenerateButton: pass

class CancelButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="✖",
            row=1,
            disabled=False
        )
    
    
    
    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.cancel(interaction)
    


class ChatGPT(discord.ui.View):
    def __init__(self, mc: MikoCore):
        super().__init__(timeout=mc.tunables('GLOBAL_VIEW_TIMEOUT'))
        self.mc = mc
        
        self.msg: discord.Message = None
        
        self.add_item(CancelButton())
    
    
    
    async def on_timeout(self) -> None:
        self.stop()



    async def cancel(self, interaction: discord.Interaction) -> None:
        cancel_test = (interaction.user.id == self.mc.user.user.id) or \
            (interaction.channel.permissions_for(interaction.user).manage_messages)

        if not cancel_test: return

        await self.msg.delete()
        await self.openai_response.close()
    
    
    
    async def ainit(self) -> None:
        pass