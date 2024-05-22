'''
Calling file for raw member remove events
'''



import discord
import logging

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
from Events.RawMemberRemove.NotifyMemberLeave import member_leave_message
LOGGER = logging.getLogger()

async def caller(payload: discord.RawMemberRemoveEvent, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_RAW_MEMBER_REMOVE'): return
    await mc.user_ainit(user=payload.user, client=client)
    
    if payload.user.id == client.user.id: pass # handle bot leaving server
    
    try: await member_leave_message(mc)
    except Exception as e: LOGGER.error(f"Error in member_leave_message: {e}")