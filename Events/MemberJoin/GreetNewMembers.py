'''
Greet new server members and announce
their unique member number
'''



import asyncio
import discord
import logging

from Database.MikoCore import MikoCore
LOGGER = logging.getLogger()

async def greet_new_members(mc: MikoCore) -> None:
    if mc.profile.feature_enabled('GREET_NEW_MEMBERS') != 1: return
    
    channel = mc.guild.guild.system_channel
    if channel is None or not channel.permissions_for(mc.guild.guild.me).send_messages: return
    
    await asyncio.sleep(1) # ensure welcome message is sent after (discord) system join message
    
    new = False if mc.user.first_join == mc.user.latest_join else True
    
    await channel.send(
        f'Hi {mc.user.user.mention}, welcome {"BACK" if new else ""} to {mc.guild.guild.name}! :tada:\n'
        f'> You are unique member `#{mc.user.member_number}`'
    )