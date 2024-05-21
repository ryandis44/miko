'''
Assign members a role when joining the server
'''



import discord
import logging

from cogs_cmd.HolidayRoles.holiday_roles import get_holiday
from Database.MikoCore import MikoCore
LOGGER = logging.getLogger()

async def role_assign(mc: MikoCore) -> None:
    if not mc.tunables('FEATURE_ENABLED_ROLE_ASSIGN') or mc.guild.role_assign is None: return
    
    try: await mc.user.user.add_roles(mc.guild.role_assign)
    except Exception as e:
        LOGGER.error(f'Failed to assign joining role to user {mc.user.user} in guild {mc.guild.guild}, removing role from DB | {e}')
        await mc.guild.set_role_assign(role_id=None)
    
    
    
    # The boys server custom implementation
    if mc.guild.profile_text != "THEBOYS": return
    
    holiday_role = mc.guild.guild.get_role(get_holiday(mc.user.user, "ROLE"))
    await mc.user.user.add_roles(holiday_role)
    
    if mc.user.user.bot:
        bot = mc.guild.guild.get_role(890642126445084702)
        await mc.user.user.add_roles(bot)