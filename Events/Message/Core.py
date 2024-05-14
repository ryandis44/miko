'''
Calling file for all message events
'''



import discord

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
from Events.Message.BigEmojis import big_emojis

async def caller(message: discord.Message, client: Bot) -> None:
    mc = MikoCore()
    if mc.tunables('PROCESS_TEXT_COMMANDS'): await client.process_commands(message) # discord.py function for handling all text commands
    if not mc.tunables('EVENT_ENABLED_ON_MESSAGE'): return
    await mc.message_ainit(message=message, client=client)
    
    if await big_emojis(mc): return # do not process message further if big emoji is created