'''
Calling file for all presence events
'''



import asyncio
import discord
import time

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot

PRESENCE_UPDATES = {}

async def caller(previous: discord.Member, current: discord.Member, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_PRESENCE_UPDATE'): return
    
    async with await presence_lock(user=current):
        await mc.user_ainit(user=current, client=client)
    


# Ensure that only one presence update is processed at a time per user
async def presence_lock(user: discord.Member) -> asyncio.Lock:
    val = PRESENCE_UPDATES.get(user.id)
    
    if val is None:
        lock = asyncio.Lock()
        PRESENCE_UPDATES[user.id] = {
            'at': int(time.time()),
            'lock': lock
        }
        return lock
    
    val['at'] = int(time.time())
    return val['lock']