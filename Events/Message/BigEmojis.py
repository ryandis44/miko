'''
Big emojis. Takes the png of the emoji, enlarges it,
and sends it in an embed to make the emoji bigger
'''



import discord

from Database.MikoCore import MikoCore
from misc.misc import sanitize_name

async def big_emojis(mc: MikoCore) -> bool:
    if mc.profile.feature_enabled('BIG_EMOJIS') != 1: return False
    if (not mc.user.do_big_emojis or mc.message.message.author.bot) or \
        mc.message.message.channel.type in mc.threads: return False
    if len(mc.message.message.content.split()) == 1 and mc.message.message.author.id != mc.user.client.user.id:
        if mc.message.message.content.startswith("<") and mc.message.message.content[1] not in ['@', '#', '/', 't']:
            try:
                auth = None
                
                # Check if the message is a reply
                # If reply, get the author of the message
                # If replying to a previous BigEmoji message,
                # grab the name of the author of the previous message
                # from the previous message's embed author
                if mc.message.message.reference is not None:
                    ref = mc.message.message.reference.resolved
                    if ref.author.id == mc.user.client.user.id:
                        try:
                            embed = ref.embeds[0]
                            auth = embed.author.name.split("→")[0]
                        except: pass
                    else:
                        auth = MikoCore()
                        await auth.user_ainit(user=ref.author, client=mc.user.client)
                        auth = auth.user.username

                await mc.message.message.delete()
                e = await __big_emoji_embed(mc, auth)
                if auth is not None: await ref.reply(embed=e, silent=True)
                else: await mc.message.message.channel.send(embed=e, silent=True)
                await mc.user.increment_statistic('BIG_EMOJIS_SENT')
                return True
            except Exception as e: print(f"Big emoji error: {e}")
    return False

async def __big_emoji_embed(mc: MikoCore, auth: str) -> discord.Embed:
        msg: discord.Message = mc.message.message
        embed = discord.Embed(color=0x2f3136) # discord dark gray
        embed.set_author(icon_url=mc.user.miko_avatar, name=f'{sanitize_name(mc.user.username)}{"" if auth is None else f" → {auth}"}')
        url, emoji_name = get_emoji_url(msg.content)
        embed.set_image(url=url)
        embed.set_footer(text=f":{emoji_name}:")
        return embed

def get_emoji_url(s: str) -> tuple:

    msg = s.split(':')
    emoji_name = msg[1]
    msg = msg[-1][:-1]

    if s[1:3] == "a:": return f"https://cdn.discordapp.com/emojis/{msg}.gif", emoji_name
    return f"https://cdn.discordapp.com/emojis/{msg}.png", emoji_name