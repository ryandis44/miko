'''
Calling file for on member join events
'''



import discord
import logging

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
LOGGER = logging.getLogger()

async def caller(member: discord.Member, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_MEMBER_JOIN'): return
    await mc.user_ainit(user=member, client=client)