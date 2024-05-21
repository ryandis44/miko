'''
Calling file for on member join events
'''



import discord

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
from Events.OnMemberJoin.RoleAssign import role_assign

async def caller(member: discord.Member, client) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_MEMBER_JOIN'): return
    await mc.user_ainit(user=member, client=client)
    
    # DOES NOT CURRENTLY ACCOUNT FOR BOT OUTAGES
    await role_assign(mc) # Assign roles to new members