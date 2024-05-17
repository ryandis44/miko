'''
Respond with a simple help message whenever Miko is mentioned
'''



from Database.MikoCore import MikoCore

async def reply_to_mention(mc: MikoCore) -> None:
    if not mc.tunables('FEATURE_ENABLED_REPLY_TO_MENTION'): return
    if mc.message.message.author.bot: return
    if mc.message.message.content == f"<@{mc.message.client.user.id}>":
        await mc.message.message.reply(f"Hello! I'm {mc.user.client.user.mention}! Type"\
            f" {mc.tunables('SLASH_COMMAND_SUGGEST_HELP')} to see what I can do!")