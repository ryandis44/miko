'''
Main file for all OpenAI textual API interactions
'''



import asyncio
import discord
import logging
import re
import tiktoken

from Database.MikoCore import MikoCore
from GenerativeAI.CachedObjects import CachedMessage
from openai import OpenAI
LOGGER = logging.getLogger()
    


class ChatGPT:
    def __init__(self, mc: MikoCore, ai_mode: dict, chats: list) -> None:
        self.mc = mc
        self.openai_client = OpenAI(api_key=mc.tunables('OPENAI_API_KEY'))
        self.ai_mode = ai_mode
        self.cached_chats = chats
        self.model = ai_mode['model']
        
        self.msg: discord.Message = None
        self.chat: list = []



    async def cancel(self, interaction: discord.Interaction) -> None:
        cancel_test = (interaction.user.id == self.mc.user.user.id) or \
            (interaction.channel.permissions_for(interaction.user).manage_messages)

        if not cancel_test: return

        await self.msg.delete()
        await self.openai_response.close()
    
    
    
    async def ainit(self) -> None:
        
        if not await self.__prep_chat(): return
        if not await self.__send_reply(): return
        await self.respond()



    async def __prep_chat(self) -> bool:
        
        try:
            
            '''
            The context buffer is used to ensure AI models are able to send their
            entire response. ChatGPT 3.5 has a max context length of 4097 tokens
            and this buffer allocates x amount of tokens to the response itself.
            '''
            
            cnt = self.ai_mode['response_tokens']
            
            # Add latest message to end (front) of chat list
            msg = f"{self.mc.user.user.mention}: {' '.join(self.mc.ai_remove_mention(self.mc.message.message.content.split()))}"
            if len(self.mc.message.message.attachments) > 0:
                val = await self.mc.ai_check_attachments(message=self.mc.message.message)
                if val is not None:
                    msg = f"{msg} {val}"
            
            system_prompt = {"role": "system", "content": self.ai_mode['prompt']}
            user_current_content = {"role": "user", "content": msg}
            cnt += self.__num_tokens_from_messages(messages=[system_prompt, user_current_content])
            
            self.chat.append(user_current_content)
            
            for m in self.cached_chats:
                # if type(m) == discord.Message:
                #     print(f">>> DISCORD: {m.content}")
                # else:
                #     print(f">>> REDIS: {m.content} {None if len(m.attachments) == 0 else m.attachments[0].data}")
                m: discord.Message|CachedMessage
                msg = None
                if m.content == "" and len(m.attachments) == 0:
                    try:
                        msg = m.embeds[0].description
                        if msg == "" or msg is None or msg == []: raise Exception
                    except: return False
                else:
                    try:
                        if re.match(r"^((<@\d{15,22}>)\s*)+$", m.content): continue # Ignore @ mentions in threads (all users)
                        if "Jump to that thread:" in m.content: return False # Ignore jump to thread message in parent channel
                        msg = ' '.join(self.mc.ai_remove_mention(m.content.split()))
                        if msg == self.mc.tunables('LOADING_EMOJI'): continue # Ignore unresponded messages
                        for embed in m.embeds:
                            if embed.description == "" or embed.description is None: continue
                            msg += " " + embed.description
                    except: pass
                
                # Decode message.txt, if applicable
                if len(m.attachments) >0:
                    val = await self.mc.ai_check_attachments(message=m)
                    if val is not None:
                        msg = f"{msg} {val}"
                    elif msg == "" or msg is None or msg == []: return False # Could cause issues. Replace with continue if so.
                
                
                # Add message to chat list
                if m.author.id == self.mc.message.message.channel.guild.me.id:
                    ct = {"role": "assistant", "content": msg}
                else:
                    # If message is >response_tokens, split responses
                    # info multiple list items. Unsure if needed yet.
                    ct = {"role": "user", "content": f"{m.author.mention}: {msg}"}
                
                
                cnt += self.__num_tokens_from_messages(messages=[ct])
                if cnt >= self.ai_mode['input_tokens']: break
                self.chat.append(ct)
            
            
            self.chat.append(system_prompt)
            self.chat.reverse()
            return True
        except Exception as e:
            LOGGER.error(f"Error initializing ChatGPT: {e}")
            return False



    async def __send_reply(self) -> bool:
        if self.mc.channel.ai_threads == "ALWAYS":
            if await self.__create_thread()



    async def __create_thread(self, content: str, embed: discord.Embed, attachments) -> bool:
        if self.mc.channel.ai_threads is None or (self.msg is not None and self.msg.channel.type in self.mc.threads): return False
        if self.mc.profile.feature_enabled('AI_THREADS') != 1: return False
        
        '''
        Miko will create a thread if:
            - It has private thread creation permission
            - AND it has manage threads permission
            - AND FINALLY the user interacting with Miko is able to
            send messages in threads.
            - OR if gpt_threads == "ALWAYS" and the above
            is satisfied
        '''
        create = self.mc.message.message.channel.permissions_for(self.mc.message.message.channel.guild.me).create_private_threads
        manage = self.mc.message.message.channel.permissions_for(self.mc.message.message.channel.guild.me).manage_threads
        user_can_send_messages = self.mc.message.message.channel.permissions_for(self.mc.user.user).send_messages_in_threads
        if self.mc.message.message.channel.type == discord.ChannelType.text and (create and manage and user_can_send_messages):
            if len(self.mc.message.message.content) > 0:
                name = ' '.join(self.mc.ai_remove_mention(self.mc.message.message.content.split()))
            else:
                name = self.mc.ai_remove_mention(self.mc.message.message.content.split())
                if len(name) > 0: name = ' '.join(name)
                else: name = ''.join(name)
            
            self.thread = await self.mc.message.message.channel.create_thread(
                name=name[0:90] if len(name) < 89 else name[0:90] + "...",
                auto_archive_duration=60,
                slowmode_delay=self.mc.tunables('GENERATIVE_AI_THREAD_SLOWMODE_DELAY'),
                reason="User-generated generative AI thread",
                invitable=True
            )
            temp = await self.thread.send(
                content=content,
                embed=embed,
                files=attachments,
                silent=True,
                allowed_mentions=discord.AllowedMentions(
                    replied_user=True,
                    users=True,
                )
                # view=self # Depreciated Miko 2.0 feature; TODO for 3.0
            )
            
            if self.msg is None:
                await self.mc.message.message.reply(
                    content=self.__thread_created_info()
                )



    def __num_tokens_from_messages(self, messages: list):
        """Return the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            LOGGER.warning("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if self.model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
            "gpt-4-0125-preview",
            "gpt-3.5-turbo-0125",
            }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif self.model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        # elif "gpt-3.5-turbo" in self.model:
        #     print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        #     return self.__num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        # elif "gpt-4" in self.model:
        #     print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        #     return self.__num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {self.model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens