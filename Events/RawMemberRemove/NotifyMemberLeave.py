'''
Send a message to system channel upon member leave
'''



import discord
import logging

from Database.MikoCore import MikoCore
LOGGER = logging.getLogger()

async def member_leave_message(mc: MikoCore) -> None:
    if not mc.profile.feature_enabled('NOTIFY_MEMBER_LEAVE'): return