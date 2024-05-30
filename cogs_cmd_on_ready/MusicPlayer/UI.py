'''
File responsible for all visuals of the music player
'''



import discord

from Database.MikoCore import MikoCore

class MikoMusic(discord.ui.View):
    
    def __init__(self, mc: MikoCore):
        self.mc = mc
        super().__init__(timeout=mc.tunables('GLOBAL_VIEW_TIMEOUT'))
        
        
        
    async def ainit(self) -> None:
        pass