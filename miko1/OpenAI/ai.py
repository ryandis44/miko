import asyncio
from io import BytesIO
import time
from openai import OpenAI
import tiktoken
import discord
import re
from Database.tunables import *
from Database.GuildObjects import CachedMessage, MikoMember, GuildProfile, AsyncDatabase, RedisCache, MikoTextChannel, MikoMessage

db = AsyncDatabase('OpenAI.ai.py')
r = RedisCache('OpenAI.ai.py')

openai_client = OpenAI(api_key=tunables('OPENAI_API_KEY'))

class RegenerateButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            style=discord.ButtonStyle.green,
            label="Regenerate",
            emoji=tunables('GENERIC_REFRESH_BUTTON'),
            custom_id="regen_button",
            row=1,
            disabled=False
        )
    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message()
        await (await interaction.original_response()).delete()
        async with interaction.channel.typing():
            await self.view.respond()

class CancelButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Cancel",
            emoji="✖",
            custom_id="cancel_button",
            row=1,
            disabled=False
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.cancel(interaction)


class MikoGPT(discord.ui.View):
    def __init__(self, mm: MikoMessage):
        super().__init__(timeout=tunables('GLOBAL_VIEW_TIMEOUT'))
        self.mm = mm
        self.chat = []
        self.response_extra_content = ""
        self.channel = mm.message.channel
        self.ctype = self.channel.type
        self.model = tunables('CHATGPT_GENERIC_MODEL')

        self.msg: discord.Message = None
        self.response = {
            'personality': None,
            'data': None
        }
        self.thread_types = [
            discord.ChannelType.public_thread,
            discord.ChannelType.private_thread,
            discord.ChannelType.news_thread
        ]
        self.add_item(CancelButton())

    async def on_timeout(self) -> None:
        # self.clear_items()
        # try: await self.msg.edit(view=self)
        # except: pass
        self.stop()


    async def cancel(self, interaction: discord.Interaction) -> None:
        cancel_test = (interaction.user.id == self.mm.user.user.id) or \
            (interaction.channel.permissions_for(interaction.user).manage_messages)

        if not cancel_test: return

        await self.msg.delete()
        await self.openai_response.close()


    async def ainit(self) -> None:
        if self.mm.message.author.bot or self.mm.message.content.startswith("!"): return
        self.gpt_threads = await self.mm.channel.gpt_threads

        __ = await self.mm.channel.gpt_personality
        if __ is None: return # For 'DISABLED'
        
        self.response['personality'] = __['prompt']
        self.model = __['model']
        self.value = __['value']
        self.input_tokens = __['input_tokens']
        self.response_tokens = __['response_tokens']

        self.t = discord.ChannelType
        match self.ctype:
            case self.t.text | self.t.voice | self.t.news | self.t.forum | self.t.stage_voice:
                if len(self.mm.message.content) > 0 and str(self.mm.channel.client.user.id) in self.mm.message.content.split()[0] and self.mm.message.author.id != self.mm.channel.client.user.id or \
                    (self.mm.message.reference is not None and self.mm.message.reference.resolved is not None and \
                        self.mm.message.reference.resolved.author.id == self.mm.channel.client.user.id):
                            if (len(self.mm.message.content.split()) <= 1 and self.mm.message.content == f"<@{str(self.mm.channel.client.user.id)}>") or \
                                (await self.mm.channel.profile).feature_enabled('CHATGPT') != 1:
                                await self.mm.message.reply(
                                    content=f"Please use {tunables('SLASH_COMMAND_SUGGEST_HELP')} for help.",
                                    silent=True
                                )
                                await self.on_timeout()
                                return

                else:
                    await self.on_timeout()
                    return


            case self.t.public_thread | self.t.private_thread | self.t.news_thread:
                if not tunables('MESSAGE_CACHING') or not tunables('FEATURE_ENABLED_CHATGPT_THREADS'): return

                try: await self.channel.fetch_member(self.mm.user.client.user.id)
                except: return

                if (len(self.mm.message.content) == 0 and len(self.mm.message.attachments) == 0) or \
                    self.response['personality'] is None: return

                if re.match(r"^((<@\d{15,22}>)\s*)+$", self.mm.message.content): return
            case _: return

        if not await self.__fetch_chats(): return
        if not await self.__send_reply(): return
        await self.respond()

    async def __send_reply(self) -> bool:
        if self.response['personality'] is None:
            if self.mm.message.reference is None:
                await self.mm.message.reply(
                    content=tunables('OPENAI_NOT_ENABLED_IN_CHANNEL'),
                    mention_author=True,
                    silent=True
                )
                return False
            else: return False



        if self.gpt_threads == "ALWAYS" and tunables('MESSAGE_CACHING'):
            if await self.__create_thread(
                content=(
                        self.__thread_info() +
                        "Generating response... " + tunables('LOADING_EMOJI')
                    ),
                embed=None,
                attachments=None
            ):
                self.response_extra_content = self.__thread_info()
                return True


        self.msg = await self.mm.message.reply(
            content=tunables('LOADING_EMOJI'),
            silent=True,
            mention_author=False,
            view=self
        )
        return True

    def __thread_created_info(self) -> str:
        return (
            f"I created a private thread that only you and I can access, {self.mm.message.author.mention}.\n"
            f"→ Jump to that thread: {self.thread.jump_url}"
        )

    def __thread_info(self) -> str:
        return (
            f"Hello {self.mm.message.author.mention}! I created a private thread that only you and "
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

    async def __check_attachments(self, message: discord.Message|CachedMessage) -> str|None:
        if len(message.attachments) == 0: return None
        if message.attachments[0].filename != "message.txt": return None
        try: return (await message.attachments[0].read()).decode()
        except:
            try: return message.attachments[0].data
            except: return None


    async def __fetch_chats(self) -> bool:

        # If not in thread, do this
        refs = await self.__fetch_replies()

        if len(refs) == 0:
            if self.ctype in THREAD_TYPES:
                refs = await self.__fetch_thread_messages()

        try:

            '''
            The CHATGPT_BUFFER_CONTEXT_AMOUNT is used to ensure ChatGPT's entire
            response is sent. ChatGPT 3.5 has a max context length of 4097 tokens
            and this buffer allocates x amount of tokens to the response itself.
            '''
            # depreciated; response length is now defined in API docs
            # cnt = tunables('CHATGPT_BUFFER_CONTEXT_AMOUNT')
            
            cnt = self.response_tokens

            # Add latest message to end of chat list
            mssg = f"{self.mm.user.user.mention}: {' '.join(self.__remove_mention(self.mm.message.content.split()))}"
            if len(self.mm.message.attachments) > 0:
                val = await self.__check_attachments(message=self.mm.message)
                if val is not None:
                    mssg = f"{mssg} {val}"

            system_personality = {"role": "system", "content": self.response['personality']}
            user_current_content = {"role": "user", "content": mssg}
            cnt += self.__num_tokens_from_messages(messages=[system_personality, user_current_content])

            self.chat.append(user_current_content)


            # Determine the string to append to chat or
            # cancel interaction if any replied messages
            # cannot be read.
            for m in refs:
                # if type(m) == discord.Message:
                #     print(f">>> DISCORD: {m.content}")
                # else:
                #     print(f">>> REDIS: {m.content} {None if len(m.attachments) == 0 else m.attachments[0].data}")
                m: discord.Message|CachedMessage
                mssg = None
                if m.content == "" and len(m.attachments) == 0:# or re.match(r"<@\d{15,30}>", m.content):
                    try:
                        mssg = m.embeds[0].description
                        if mssg == "" or mssg is None or mssg == []: raise Exception
                    except: return False
                else:
                    try:
                        if re.match(r"^((<@\d{15,22}>)\s*)+$", m.content): continue # Ignore @ mentions in threads (all users)
                        if "Jump to that thread:" in m.content: return False # Ignore jump to thread message in parent channel
                        mssg = ' '.join(self.__remove_mention(m.content.split()))
                        if mssg == tunables('LOADING_EMOJI'): continue # ignore unresponded messages
                        for embed in m.embeds:
                            if embed.description == "" or embed.description is None: continue
                            mssg += " " + embed.description
                    except: pass


                # Decode message.txt, if applicable
                if len(m.attachments) > 0:
                    val = await self.__check_attachments(message=m)
                    if val is not None:
                        mssg = f"{mssg} {val}"
                    elif mssg == "" or mssg is None or mssg == []: return False # Could cause issues. Replace with continue if so



                # Add message to chat list
                if m.author.id == self.mm.channel.guild.me.id:
                    ct = {"role": "assistant", "content": mssg}
                else:
                    # If message is >response_tokens tokens, split responses
                    # into multiple list items. dont know if needed yet
                    ct = {"role": "user", "content": f"{m.author.mention}: {mssg}"}


                cnt += self.__num_tokens_from_messages(messages=[ct])
                if cnt >= self.input_tokens: break 
                self.chat.append(ct)


            self.chat.append(system_personality)
            self.chat.reverse()
            return True
        except Exception as e:
            print(f"Error whilst fetching chats [ChatGPT]: {e}")
            return False


    async def __fetch_thread_messages(self) -> list:
        if not tunables('MESSAGE_CACHING'): return
        messages = await r.search(
            query=self.channel.id,
            type="JSON_THREAD_ID",
            index="by_thread_id",
            limit=tunables('CHATGPT_THREAD_MESSAGE_LIMIT')
        )

        refs = []
        for m in messages:
            m = CachedMessage(m=loads(m['json']))
            if (m.content != "" or len(m.attachments) > 0 or len(m.embeds) > 0) and m.id != self.mm.message.id:
                refs.append(m)
        return refs


    async def __fetch_replies(self) -> list:
        try:
            refs = []
            if self.mm.message.reference is not None:

                refs = [self.mm.message.reference.resolved]

                i = 0
                while True:
                    if refs[-1].reference is not None and i <= tunables('CHATGPT_MAX_REPLIES_CHAIN'):

                        cmsg = CachedMessage(message_id=refs[-1].reference.message_id)
                        await cmsg.ainit()
                        if refs[-1].reference.cached_message is not None:
                            m: discord.Message = refs[-1].reference.cached_message
                        elif cmsg.content != "" or len(cmsg.attachments) > 0 or len(cmsg.embeds) > 0:
                            m = cmsg
                        else:
                            m: discord.Message = await self.channel.fetch_message(refs[-1].reference.message_id)
                            if m is None:
                                i+=1
                                continue
                            mm = MikoMessage(message=m, client=self.mm.channel.client)
                            await mm.ainit(check_exists=False)
                        refs.append(m)
                    else: break
                    i+=1

            return refs
        except Exception as e:
            print(f"Error whilst fetching message replies [ChatGPT]: {e}")
            return []

    def __remove_mention(self, msg: list) -> list:
        for i, word in enumerate(msg):
            if word in [f"<@{str(self.mm.channel.client.user.id)}>"]:
                # Remove word mentioning Miko
                msg.pop(i)
        return msg


    def __num_tokens_from_messages(self, messages: list):
        """Return the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
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


    async def respond(self, retries=0) -> None:
        self.clear_items()
        # if await self.mm.channel.gpt_mode == "NORMAL":
        #     self.add_item(RegenerateButton())

        # print("*************")
        # print(f"GPT Threads Mode: {self.gpt_threads}")
        # print(f"GPT Model: {self.model}")
        # for i, c in enumerate(self.chat):
        #     print(f">> {i+1} {c}")
        # print("*************")

        try:
            self.openai_response = asyncio.to_thread(self.__openai_interaction)
            await self.openai_response

            resp_len = len(self.response['data'])
            if resp_len >= 750 and resp_len <= 3999:
                embed = await self.__embed()


                thread_content = (self.__thread_info() +
                    "Please see my response below:"
                )
                if await self.__create_thread(content=thread_content, embed=await self.__embed(), attachments=None): return

                await self.msg.edit(
                        content=None if self.response_extra_content == "" else self.response_extra_content + "Please see my response below:",
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(
                            replied_user=True,
                            users=True
                        ),
                        view=self
                    )
                return

            elif resp_len >= 4000:
                b = bytes(self.response['data'], 'utf-8')
                attachments = [discord.File(BytesIO(b), "message.txt")]

                if await self.__create_thread(
                        content=(self.__thread_info() +
                            "The response to your prompt was too long. I have sent it in this "
                            "`message.txt` file. You can view on PC or Web (or Mobile if you "
                            "are able to download the file)."
                        ),
                        embed=None,
                        attachments=attachments
                    ): return

                await self.msg.edit(
                    content=(self.response_extra_content +
                            "The response to your prompt was too long. I have sent it in this "
                            "`message.txt` file. You can view on PC or Web (or Mobile if you "
                            "are able to download the file)."
                        ),
                    attachments=attachments,
                    view=self
                )
                return
            else:
                embed = None
                content = self.response['data']

            await self.msg.edit(
                content=content if self.response_extra_content == "" else self.response_extra_content + content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    replied_user=True,
                    users=True
                ),
                view=self
            )
            await self.mm.user.increment_statistic('REPLY_TO_MENTION_OPENAI')
        except Exception as e:

            if retries <= 5 and type(Exception) is type:

                try:
                    await self.msg.edit(content=f"`Error. Retrying...`")
                except: pass

                await asyncio.sleep(2)

                try:
                    await self.msg.edit(content=tunables('LOADING_EMOJI'))
                except: pass

                await self.respond(retries + 1)
                return
            await self.mm.user.increment_statistic('REPLY_TO_MENTION_OPENAI_REJECT')
            try:
                await self.msg.edit(
                    content=f"{tunables('GENERIC_APP_COMMAND_ERROR_MESSAGE')[:-1]}: {e}",
                    allowed_mentions=discord.AllowedMentions(
                        replied_user=False,
                        users=False
                    ),
                    view=None
                )
            except: pass

    async def __create_thread(self, content: str, embed: discord.Embed, attachments) -> bool:

        if self.gpt_threads is None or (self.msg is not None and self.msg.channel.type in THREAD_TYPES): return False
        if (await self.mm.channel.profile).feature_enabled('CHATGPT_THREADS') != 1: return False

        '''
        Miko will create a thread if:
            - It has private thread creation permission
            - AND it has manage threads permission
            - AND FINALLY the user interacting with Miko is able to
            send messages in threads.
            - OR if gpt_threads == "ALWAYS" and the above
            is satisfied
        '''
        create = self.channel.permissions_for(self.channel.guild.me).create_private_threads
        manage = self.channel.permissions_for(self.channel.guild.me).manage_threads
        user_can_send_messages = self.channel.permissions_for(self.mm.message.author).send_messages_in_threads
        if self.ctype == discord.ChannelType.text and (create and manage and user_can_send_messages):
            if len(self.mm.message.content) > 90:
                name = ' '.join(self.__remove_mention(self.mm.message.content.split()))
            else:
                name = self.__remove_mention(self.mm.message.content.split())
                if len(name) > 1: name = ' '.join(name)
                else: name = ''.join(name)

            self.thread = await self.channel.create_thread(
                name=name[0:90] if len(name) < 89 else name[0:90] + "...",
                auto_archive_duration=60,
                slowmode_delay=tunables('CHATGPT_THREAD_SLOWMODE_DELAY'),
                reason=f"User requested ChatGPT response",
                invitable=True
            )
            temp = await self.thread.send(
                content=content,
                embed=embed,
                files=attachments,
                silent=True,
                allowed_mentions=discord.AllowedMentions(
                    replied_user=True,
                    users=True
                ),
                view=self
            )

            if self.msg is None:
                await self.mm.message.reply(
                    content=self.__thread_created_info(),
                    embed=None,
                    view=None
                )
                self.msg = temp
                return True

            await self.msg.edit(
                embed=None,
                view=None,
                content=self.__thread_created_info()
            )
            return True
        return False

    async def __embed(self) -> discord.Embed:
        temp = []

        temp.append(f"{self.response['data']}")

        embed = discord.Embed(
            description=''.join(temp),
            color=GLOBAL_EMBED_COLOR
        )
        embed.set_author(
            icon_url=await self.mm.user.user_avatar,
            name=f"Generated by {await self.mm.user.username}"
        )
        embed.set_footer(
            text=f"{self.value.upper()}  •  {self.model}  •  Max Context Length {self.input_tokens:,} Tokens"
        )
        return embed

    def __openai_interaction(self) -> None:
        resp = openai_client.chat.completions.create(
                model=self.model,
                messages=self.chat
            )

        text = resp.choices[0].message.content
        self.response['data'] = text