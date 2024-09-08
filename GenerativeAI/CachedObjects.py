import logging

from Database.MikoCore import MikoCore
from Database.Redis import RedisCache
r = RedisCache(__file__)
LOGGER = logging.getLogger()



class CachedMessage:
    def __init__(self, message_id: int=None, m: dict=None) -> None:
        self.mc = MikoCore()
        self.message_id = message_id
        self.m = m
        self.id: int = None
        self.content: str = None
        self.embeds = []
        self.author: CachedUser = None
        self.thread: CachedChannel = None
        self.channel: CachedChannel = None
        self.guild: CachedGuild = None
        self.reference: CachedReference = None
        self.attachments = []
        if m is not None:
            try: self.__assign_attributes()
            except Exception as e: LOGGER.error(f"Cached error {e}")
    
    async def ainit(self):
        if not self.mc.tunables('MESSAGE_CACHING'): return
        self.m = await r.get(key=f"m:{self.message_id}", type="JSON")
        if self.m is None: return
        self.__assign_attributes()
    
    def __assign_attributes(self):
        self.id = int(self.m['id'])
        self.content = self.m['content']
        self.author = CachedUser(name=self.m['author']['name'], id=int(self.m['author']['id']))
        self.created_at = self.m['created_at']
        for embed in self.m['embeds']:
            self.embeds.append(
                CachedEmbed(embed=embed)
            )
        if self.m['reference_id'] is not None and self.m['reference_id'] != "null":
            self.reference = CachedReference(message_id=int(self.m['reference_id']))
        for attachment in self.m['attachments']:
            self.attachments.append(
                CachedAttachment(attachment=attachment)
            )
        if self.m['thread'] is not None and self.m['thread'] != "null":
            self.thread = CachedChannel(
                name=self.m['thread']['name'],
                type=self.m['thread']['type'],
                id=self.m['thread']['id']
            )
        self.channel = CachedChannel(
            name=self.m['channel']['name'],
            type=self.m['channel']['type'],
            id=self.m['channel']['id']
        )
        self.guild = CachedGuild(
            name=self.m['guild']['name'],
            id=self.m['guild']['id'],
            owner=CachedUser(name=self.m['guild']['owner']['name'], id=int(self.m['guild']['owner']['id']))
        )



class CachedUser:
    def __init__(self, name: str, id: int):
        self.name=name
        self.id=id
        self.mention = f"<@{id}>"
    def __str__(self) -> str: return self.name



class CachedChannel:
    def __init__(self, name: str, type: str, id: int):
        self.name=name,
        self.type=type,
        self.id=id
    def __str__(self) -> str: return self.name



class CachedGuild:
    def __init__(self, name: str, id: int, owner: CachedUser):
        self.name=name
        self.id=id
        self.owner = owner
    def __str__(self) -> str: return self.name



class CachedReference:
    def __init__(self, message_id: int) -> None:
        self.message_id=message_id
        self.cached_message = None



class CachedEmbed:
    def __init__(self, embed: dict) -> None:
        self.description = embed['description']



class CachedAttachment:
    def __init__(self, attachment: dict):
        self.data = attachment['data']
        self.filename = attachment['filename']