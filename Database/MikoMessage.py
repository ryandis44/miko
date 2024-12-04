'''
This class is responsible for handling all guild data
'''



import aiohttp
import discord
import logging

from Database.MySQL import AsyncDatabase
from Database.Redis import RedisCache
from discord.ext.commands import Bot
from io import BytesIO
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()
r = RedisCache(__file__)



class MikoMessage:
    
    def __init__(self) -> None:
        self.message: discord.Message = None
        self.client: Bot = None
        self.t = discord.ChannelType
        self.threads = [self.t.public_thread, self.t.private_thread, self.t.news_thread]
    
    
    
    def __str__(self) -> str: return f"MikoMessage | {self.message.author.name}"
    
    
    
    async def ainit(self, message: discord.Message, client: Bot) -> None:
        self.message = message
        self.client = client
    
    
    
    async def cache_message(self) -> None:
        m = await r.get(key=f"m:{self.message.id}", type="JSON")
        if m is None:
            
            embeds = []
            if len(self.message.embeds) > 0:
                for embed in self.message.embeds:
                    if embed.description is None or embed.description == "": continue
                    embeds.append({
                        'description': embed.description
                    })
            
            attachments = []
            if len(self.message.attachments) > 0 and self.message.attachments[0].filename == "message.txt":
                try:
                    attachments.append({
                        'filename': "message.txt",
                        'data': (await self.message.attachments[0].read()).decode()
                    })
                except: pass
            
            await r.set(
                key=f"m:{self.message.id}",
                type="JSON",
                value={
                    'id': str(self.message.id),
                    'content': self.message.content,
                    'created_at': int(self.message.created_at.timestamp()),
                    'reference_id': None if self.message.reference is None else str(self.message.reference.message_id),
                    'attachments': attachments,
                    'embeds': embeds,
                    'author': {
                        'name': str(self.message.author),
                        'id': str(self.message.author.id)
                    },
                    'thread': None if self.message.channel.type not in self.threads else {
                        'name': str(self.message.channel.name),
                        'type': str(self.message.channel.type),
                        'id': str(self.message.channel.id),
                    },
                    'channel': {
                        'name': str(self.message.channel.name),
                        'type': str(self.message.channel.type),
                        'id': str(self.message.channel.id)
                    } if self.message.channel.type not in self.threads else {
                        'name': str(self.message.channel.parent.name),
                        'type': str(self.message.channel.parent.type),
                        'id': str(self.message.channel.parent_id)
                    },
                    'guild': {
                        'name': str(self.message.guild),
                        'id': str(self.message.guild.id),
                        'owner': {
                            'name': str(self.message.guild.owner),
                            'id': str(self.message.guild.owner.id)
                        }
                    }
                }
            )
        else: pass # update cache?



    async def assign_cached_message_to_thread(self, thread: discord.Thread) -> None:
        m = await r.get(key=f"m:{self.message.id}", type="JSON")
        if m is None: return
        # Assign thread
        await r.set(
            key=f"m:{self.message.id}",
            type="JSON",
            path="$.thread",
            value=None if thread.type not in self.threads else {
                'name': str(thread.name),
                'type': str(thread.type),
                'id': str(thread.id)
            }
        )
    
    
    
    async def edit_cached_message(self, payload: discord.RawMessageUpdateEvent) -> None:
        self.payload = payload

        m = await r.get(key=f"m:{self.payload.message_id}", type="JSON")
        if m is None: return
        # Update message content
        await r.set(
            key=f"m:{self.payload.message_id}",
            type="JSON",
            path="$.content",
            value=self.payload.data['content']
        )
        # Update attachments
        data = await self.__get_attachments()
        await r.set(
            key=f"m:{self.payload.message_id}",
            type="JSON",
            path="$.attachments",
            value=[{
                'filename': "message.txt",
                'data': data
            }] if data != [] else []
        )
        # Update embed description
        embeds = []
        if len(self.payload.data['embeds']) > 0:
            for embed in self.payload.data['embeds']:
                if embed['description'] is None or embed['description'] == "": continue
                embeds.append({
                    'description': embed['description']
                })
        await r.set(
            key=f"m:{self.payload.message_id}",
            type="JSON",
            path="$.embeds",
            value=embeds
        )



    async def delete_cached_message(self, payload: discord.RawMessageDeleteEvent) -> None:
        await r.delete(key=f"m:{payload.message_id}")



    async def __get_attachments(self) -> str:
        if len(self.payload.data['attachments']) > 0:
            for attachment in self.payload.data['attachments']:
                if attachment['filename'] != "message.txt": continue
                async with aiohttp.ClientSession() as ses:
                    async with ses.get(attachment['url']) as r:
                        if r.status in range(200, 299):
                            data = BytesIO(await r.read())
                            try: data = data.getvalue().decode()
                            except: return []
                            return data
        return []