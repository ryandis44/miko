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
import logging

from Database.MikoCore import MikoCore
from Database.Redis import RedisCache
from GenerativeAI.CachedObjects import CachedMessage
from GenerativeAI.OpenAI.ChatGPT import ChatGPT
from json import loads
LOGGER = logging.getLogger()
r = RedisCache(__file__)



############################################################################################################



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



class GenerativeAI(discord.ui.View):
    def __init__(self, mc: MikoCore) -> None:
        self.mc = mc
        self.t = discord.ChannelType
        super().__init__(timeout=mc.tunables('GLOBAL_VIEW_TIMEOUT'))



    async def on_timeout(self) -> None: self.stop()
    
    
    
    async def ainit(self) -> None:
        
        # Do not run any of this code if AI is disabled
        if self.mc.channel.ai_mode == "DISABLED": return
        
        try: self.ai_mode = self.mc.tunables(f'GENERATIVE_AI_MODE_{self.mc.channel.ai_mode}')
        except:
            await self.mc.channel.set_ai_mode(mode="DISABLED")
            return
        
        
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
                - Get context for the AI model (chat history); this is the message's content
        
        
        If a thread and:
            - Message content is not empty
            - Message is not from Miko
        Then:
            - Get context for the AI model (chat history); this is the thread's messages
        '''
        match self.mc.message.message.channel.type:
            
            case self.t.text | self.t.voice | self.t.news | self.t.forum | self.t.stage_voice:
                # If not a thread and ...
                if len(self.mc.message.message.content) > 0 and str(self.mc.channel.client.user.id) in self.mc.message.message.content.split()[0] \
                    and self.mc.message.message.author.id != self.mc.channel.client.user.id or (self.mc.message.message.reference is not None and \
                        self.mc.message.message.reference.resolved is not None and self.mc.message.message.reference.resolved.author.id == self.mc.channel.client.user.id):
                        # then ...
                        
                        # Additionally if ...
                        if (len(self.mc.message.message.content.split()) <= 1 and self.mc.message.message.content == f"<@{str(self.mc.channel.client.user.id)}>"):
                            await self.on_timeout()
                            return
                else:
                    await self.on_timeout()
                    return
            
            case self.t.public_thread | self.t.private_thread | self.t.news_thread:
                if not self.mc.tunables('FEATURE_ENABLED_AI_THREADS'):
                    await self.mc.message.message.reply('AI_THREADS_DISABLED_MESSAGE')
                    return
                
                try: await self.mc.message.message.channel.fetch_member(self.mc.user.client.user.id)
                except: return
                
                if (len(self.mc.message.message.content) == 0 and len(self.mc.message.message.attachments) == 0): return
            
            case _: # Unknown channel type, disable AI
                try: await self.mc.channel.set_ai_mode(mode="DISABLED")
                except: pass
                return

        await self.__fetch_chats()

        '''
        Branch out to the different AI models and APIs. At this point in the
        code, all generalized processing has been done and model-specific
        operations can be performed.
        '''
        match self.ai_mode['api']:
            
            case "openai": await ChatGPT(mc=self.mc, ai_mode=self.ai_mode, chats=self.chats).ainit()
            
            case "mikoapi": LOGGER.critical("MikoAPI (Generative AI) is not yet implemented.")
            
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



    async def __fetch_chats(self) -> bool:
        
        self.chats = await self.__fetch_replies()
        
        if len(self.chats) == 0:
            if self.mc.message.message.channel.type in self.mc.threads: # if in a thread
                self.chats = await self.__fetch_thread_messages()
        return True

    async def __fetch_replies(self) -> list:
        
        try:
            replies = []
            if self.mc.message.message.reference is not None:
                replies = [self.mc.message.message.reference.resolved]
                
                i = 0
                while True:
                    if replies[-1].reference is not None and i <= self.mc.tunables('GENERATIVE_AI_MAX_REPLIES_CHAIN'):
                        cmsg = CachedMessage(message_id=replies[-1].reference.message_id)
                        await cmsg.ainit()
                        if replies[-1].reference.cached_message is not None:
                            m: discord.Message = replies[-1].reference.cached_message
                        elif cmsg.content != "" or len(cmsg.attachments) > 0 or len(cmsg.embeds) > 0:
                            m = cmsg
                        else:
                            m: discord.Message = await self.mc.message.message.channel.fetch_message(replies[-1].reference.message_id)
                            if m is None:
                                i+=1
                                continue
                            await cmsg.mc.message.ainit(message=m, client=self.mc.channel.client)
                            await cmsg.mc.message.cache_message()
                        replies.append(m)
                    else: break
                    i+=1
            return replies
        except Exception as e:
            LOGGER.error(f"Error fetching replies: {e}")
            return []



    async def __fetch_thread_messages(self) -> list:
        messages = await r.search(
            query=self.mc.message.message.channel.id,
            type="JSON_THREAD_ID",
            index="by_thread_id",
            limit=self.mc.tunables('GENERATIVE_AI_MAX_REDIS_QUERIED_THREAD_MESSAGES')
        )
        
        replies = []
        for m in messages:
            m = CachedMessage(m=loads(m['json']))
            if (m.content != "" or len(m.attachments) > 0 or len(m.embeds) > 0) and m.id != self.mc.message.message.id:
                replies.append(m)
        return replies