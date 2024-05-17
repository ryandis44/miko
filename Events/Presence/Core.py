'''
Calling file for all presence events
'''



import discord

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot

async def caller(previous: discord.Member, current: discord.Member, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_PRESENCE_UPDATE'): return
    await mc.user_ainit(user=current, client=client)