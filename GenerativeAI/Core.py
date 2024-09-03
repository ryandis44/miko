'''
Main file for determining the model and API to use for
generative AI. This file is the main entry point for
all generative AI.

If any generative AI is enabled in a channel, **all
messages will be cached for 90 days in Redis**. This
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
        
        # Do not run any of this code if AI is disabled
        if self.mc.channel.ai_mode == "DISABLED": return
        
        '''
        If:
            - The message is from a bot that is not Miko
            - The message is from discord (system message)
            - The message is intentionally ignored (starts with '!')
        Then return and do not:
            - Cache the message
            - Generate a response
            
        Else:
            - Cache the message and proceed
        '''
        if (self.mc.message.message.author.bot and self.mc.message.message.author.id != self.mc.message.client.user.id) \
            or self.mc.message.message.author.system or self.mc.message.message.content.startswith(self.mc.tunables('GENERATIVE_AI_MESSAGE_IGNORE_CHAR')): return
        
        await self.mc.message.cache_message()
        
        
        '''
        If not a thread and:
            - Message content is not empty
            - Message content contains a mention to Miko (first word)
            - Message is not from Miko or the message is referencing a message
              from Miko
        Then:
            Additionally if:
                - The message only contains a mention to Miko and does not have a prompt
            Then:
                - Return and do not generate a response
            Else:
                - Proceed to generate a response
        
        
        If a thread and:
            - Message content is not empty
            - Message is not from Miko
        Then:
            - Proceed to generate a response
        '''
        match self.mc.channel.channel.type:
            
            case self.t.text | self.t.voice | self.t.news | self.t.forum | self.t.stage_voice:
                # If not a thread and ...
                if len(self.mc.message.message.content) > 0 and str(self.mc.channel.client.user.id) in self.mc.message.message.content.split()[0] \
                    and self.mc.message.message.author.id != self.mc.channel.client.user.id or (self.mc.message.message.reference is not None and \
                        self.mc.message.message.reference.resolved is not None and self.mc.message.message.reference.resolved.author.id == self.mc.channel.client.user.id):
                        # then ...
                        
                        # Additionally if ...
                        if (len(self.mc.message.message.content.split()) <= 1 and self.mc.message.message.content == f"<@{str(self.mc.channel.client.user.id)}>"):
                            # then ...
                            return
            # else ... (continue to generate a response)
            
            case self.t.public_thread | self.t.private_thread | self.t.news_thread:
                if not self.mc.tunables('FEATURE_ENABLED_AI_THREADS'):
                    await self.mc.message.message.reply('AI_THREADS_DISABLED_MESSAGE')
                    return
                
                try: await self.mc.channel.channel.fetch_member(self.mc.user.client.user.id)
                except: return
                
                if (len(self.mc.message.message.content) == 0 and len(self.mc.message.message.attachments) == 0): return
            
            case _: # Unknown channel type, disable AI
                try: await self.mc.channel.set_ai_mode(mode="DISABLED")
                except: pass
                return
            

        ##### Get context for the AI model (chat history) #####
















        try: api = self.mc.tunables(f'GENERATIVE_AI_MODE_{self.mc.channel.ai_mode}')['api']
        except: api = self.mc.tunables(f'GENERATIVE_AI_MODE_DISABLED')['api']
        match api:
            
            case "openai":
                print("OpenAI API")
            
            case "mikoapi":
                print("Miko API")
                
            case "none": return # AI is disabled, return
            
            # Invalid API, revert to disabled
            case _:
                try: await self.mc.channel.set_ai_mode(mode="DISABLED")
                except: pass



    def __thread_info(self) -> str:
        return (
            f"Hello {self.mc.message.message.author.mention}! I created a private thread that only you and "
            "I can see so I can better help answer your questions.\n\n"
            "Private threads are similar to a regular Group DM. If you would like to invite someone "
            "to this thread, just @ mention them and they will appear. They will be able to invite anyone else from "
            "this server once added. You and anyone else in this thread can leave it by right-clicking (or long pressing) "
            "on the thread in the channels side menu.\n\n"
            "Additionally, if you would like to message in this thread without me reading the message and responding to it, "
            "put an exclamation mark `!` at the beginning of your message and I will ignore it.\n\n"
            "Also, __**no need to @ mention me in this thread**__. I will respond to all messages that are not just an @ mention "
            "(for adding people to this thread)."
            "\n\n"
        )