'''
Calling file for on member join events
'''



import discord
import logging

from Database.MikoCore import MikoCore
from discord.ext.commands import Bot
from Events.MemberJoin.GreetNewMembers import greet_new_members
from Events.MemberJoin.RoleAssign import role_assign
LOGGER = logging.getLogger()

async def caller(member: discord.Member, client: Bot) -> None:
    mc = MikoCore()
    if not mc.tunables('EVENT_ENABLED_ON_MEMBER_JOIN'): return
    await mc.user_ainit(user=member, client=client)
    
    # DOES NOT CURRENTLY ACCOUNT FOR BOT OUTAGES
    try: await role_assign(mc) # Assign roles to new members
    except Exception as e: LOGGER.error(f"Error in role_assign: {e}")
    
    # try: await greet_new_members(mc) # Greet new members
    # except Exception as e: LOGGER.error(f"Error in greet_new_members: {e}")