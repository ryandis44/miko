'''
Greet new server members and announce
their unique member number
'''



import discord
import logging

from Database.MikoCore import MikoCore
LOGGER = logging.getLogger()

async def greet_new_members(mc: MikoCore) -> None:
    if mc.profile.feature_enabled('GREET_NEW_MEMBERS') != 1: return