'''
Main file for determining the model and API to use for
generative AI. This file is the main entry point for
all generative AI.

If any generative AI is enabled in a channel, **all
messages will be cached for 30 days in Redis**. This
is to ensure that the model has enough data to generate
a response and in a timely manner.
'''



import discord

from Database.MikoCore import MikoCore

class GenerativeAI:
    def __init__(self, mc: MikoCore) -> None:
        self.mc = mc
    
    
    
    async def ainit(self) -> None:
        
        # Do not cache messages if generative AI is not enabled
        if self.mc.channel.text_ai_mode is None: return # or image_ai_mode is None
        
        '''
        If:
            - The message is from a bot that is not Miko
            - The message is from discord
            - The message is intentionally ignored (starts with '!')
        Then return and do not:
            - Cache the message
            - Generate a response
        '''
        if (self.mc.message.message.author.bot and self.mc.message.message.author.id != self.mc.message.client.user.id) \
            or self.mc.message.message.author.system or self.mc.message.message.content.startswith("!"): return
        
        await self.mc.message.cache_message()