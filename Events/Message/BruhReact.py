'''
Respond with a simple help message whenever Miko is mentioned
'''



import asyncio
import re

from Database.MikoCore import MikoCore

async def bruh_react(mc: MikoCore) -> None:
    if mc.profile.feature_enabled('BRUH_REACT') != 1 or mc.user.user.bot: return
    for word in mc.tunables('BRUH_REACT_WORDS').split():
        react_regex =  rf".*\b{word}\b.*"
        if re.match(react_regex, mc.message.message.content.lower()) or word == mc.message.message.content.lower():
            emoji = [
                "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
                "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
                "\N{REGIONAL INDICATOR SYMBOL LETTER H}"
            ]
            for i, letter in enumerate(emoji):
                if i > 0: await asyncio.sleep(0.5)
                await mc.message.message.add_reaction(letter)
            break