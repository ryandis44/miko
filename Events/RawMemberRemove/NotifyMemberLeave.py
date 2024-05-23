'''
Send a message to system channel upon member leave
If no system channel, do nothing

Additionally, YMCA servers have generic leave
messages
'''



import logging
import random

from Database.MikoCore import MikoCore
LOGGER = logging.getLogger()

async def member_leave_message(mc: MikoCore) -> None:
    if mc.profile.feature_enabled('NOTIFY_MEMBER_LEAVE') != 1 or mc.guild.guild.system_channel is None: return
    
    temp = []
    temp.append(
        f"{mc.user.user.mention}『`{mc.user.user.name}`』left"
    )
    
    match mc.guild.profile_text:
        
        case "YMCA": pass
        case _:
            match random.randint(0, 6):
                case 0: temp.append(" :pray:")
                case 1: temp.append(". Thank God")
                case 2: temp.append(". Finally!")
                case 3:
                    if mc.guild.profile_text == "THEBOYS": temp.append(". Hector scared them off")
                    else: temp.append(". They got scared off")
                case 4: temp.append(". Good riddance")
                case 5: temp.append(". Oh no! Anyway...")
                case 6: temp.append(". I thought they would never leave... :triumph:")
    
    await mc.guild.guild.system_channel.send("".join(temp))