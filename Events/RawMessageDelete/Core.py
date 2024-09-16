'''
Calling file for raw message delete events
'''



import discord
import logging

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
LOGGER = logging.getLogger()

async def caller(payload: discord.RawMessageDeleteEvent, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_RAW_MESSAGE_DELETE'): return
    
    await mc.message.delete_cached_message(payload=payload)