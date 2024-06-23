'''
Calling file for raw member remove events
'''



import discord
import logging

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
LOGGER = logging.getLogger()

async def caller(payload: discord.RawMessageUpdateEvent, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_RAW_MESSAGE_EDIT'): return
    
    await mc.message.edit_cached_message(payload)