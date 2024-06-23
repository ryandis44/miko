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
        self.t = discord.ChannelType
    
    
    
    async def ainit(self) -> None:
        
        # Do not cache messages if generative AI is not enabled
        if self.mc.channel.ai_mode == "DISABLED": return
        
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
            or self.mc.message.message.author.system or self.mc.message.message.content.startswith(self.mc.tunables('GENERATIVE_AI_MESSAGE_IGNORE_CHAR')): return
        
        await self.mc.message.cache_message()
        
        
        '''
        If not a thread and:
            - Message content is not empty
            - Message content contains a mention to Miko
            - Message is not from Miko or the message is referencing a message
              from Miko
        '''
        match self.mc.channel.channel.type:
            
            case self.t.text | self.t.voice | self.t.news | self.t.forum | self.t.stage_voice:
                print("Not Thread")
            
            case self.t.public_thread | self.t.private_thread | self.t.news_thread:
                print("Thread")
            
            case _:
                print("Unknown Channel Type")
                return
            

        try: api = self.mc.tunables(f'GENERATIVE_AI_MODE_{self.mc.channel.ai_mode}')['api']
        except: api = self.mc.tunables(f'GENERATIVE_AI_MODE_DISABLED')['api']
        match api:
            
            case "openai":
                print("OpenAI API")
            
            case "mikoapi":
                print("Miko API")
            
            # Invalid API, revert to disabled
            case _: await self.mc.channel.set_ai_mode(mode="DISABLED")