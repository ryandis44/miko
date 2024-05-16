'''
Help command
'''



import discord
import logging
import os

from Database.MikoCore import MikoCore
from discord import app_commands
from discord.ext import commands
LOGGER = logging.getLogger()

class HelpCog(commands.Cog):
    def __init__(self, client): self.client: discord.Client = client


    @app_commands.command(name="help", description=f"{os.getenv('APP_CMD_PREFIX')}Miko Help")
    @app_commands.guild_only
    @app_commands.describe(
        category="Select a category for a more detailed help menu"
    )
    @app_commands.choices(
    category=[
        app_commands.Choice(name='Playtime/Voicetime', value='ptvt'),
        # app_commands.Choice(name='Polls', value='polls'),
        app_commands.Choice(name='ChatGPT', value='chatgpt'),
    ])
    async def h(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        try: await help(interaction=interaction, category=category)
        except Exception as e: LOGGER.error(f"Error sending help command: {e}")


    @app_commands.command(name="mhelp", description=f"{os.getenv('APP_CMD_PREFIX')}Miko Help")
    @app_commands.guild_only
    @app_commands.describe(
        category="Select a category for a more detailed help menu"
    )
    @app_commands.choices(
    category=[
        app_commands.Choice(name='Playtime/Voicetime', value='ptvt'),
        # app_commands.Choice(name='Polls', value='polls'),
        app_commands.Choice(name='ChatGPT', value='chatgpt'),
    ])
    async def mh(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        try: await help(interaction=interaction, category=category)
        except Exception as e: LOGGER.error(f"Error sending help command: {e}")



    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=interaction.client, check_exists=False)
        await interaction.response.send_message(content=f"{mc.tunables('LOADING_EMOJI')}", ephemeral=True)
        await mc.user.increment_statistic('HELP_COMMAND')
        return True



async def setup(client: commands.Bot):
    await client.add_cog(HelpCog(client))



async def help(interaction: discord.Interaction, category) -> None:

    msg = await interaction.original_response()

    mc = MikoCore()
    await mc.user_ainit(user=interaction.user, client=interaction.client)

    temp = []

    if category is not None: category = category.value

    match category:
        
        case "ptvt":
            temp.append(
                f":video_game: Playtime and :microphone2: Voicetime is tracked automatically for all users in all guilds with {interaction.client.user.mention}. These settings "
                "can be changed at any time using `/settings`."
                "\n\n"
                "The `/playtime` and `/voicetime` commands supports several arguments, allowing for advanced searches. Using "
                f"this command without any arguments will pull up your own activity since {interaction.client.user.mention} "
                "began tracking it. By default, playtime shows entries longer than 5 minutes and voicetime shows entries "
                "longer than 1 minute."
                "\n\n"
                "As mentioned previously, tracking is available in all guilds and its __tracking cannot be "
                "overridden by anyone__, including the guild owner (i.e. if you disable it, the guild owner "
                "cannot enable it)."
                "\n\n"
                f"You are in complete control of whether {interaction.client.user.mention} "
                "tracks your playtime and voice activities. Activity that has already been tracked is permanent and "
                "cannot be modified by anyone."
                "\n\n"
                "__**Parameter information**__:\n"
                "> • `playtime` & `voicetime`: These parameters take a time value: `<1h`, `<3d`, and a special parameter `all`, which shows all entries >1s. For example, if you "
                "want to search for activity entries that are longer than 5 hours, that would look like `>5h`. Less than "
                "5 hours: `<5h`, more than 3 days: `>3d`, all results: `all`"
                "\n> \n"
                "> • `scope`: This parameter allows you to search `Global` (playtime only), `Guild`, or `User`. The global scope will "
                f"allow you to search for entries from all users tracked by {interaction.client.user.mention}, guild scope will search "
                "for entries by users in the current guild, and user will search for your own entries (default)."
            )
        
        case "polls":
            temp.append(
                f"{interaction.client.user.mention} supports creating polls with the creator having full control "
                "over these polls."
                "\n\n"
                "Each poll can be set to last up to 24-hours. When a poll expires, the "
                "creator of this poll will be mentioned along with the results."
                "\n\n"
                "Polls can be ended early by pressing the red `End` button. The creator of a poll "
                "can end their poll at any time using this, as well as users that have the "
                "`Mange Messages` permission in the channel the poll was created in."
                "\n\n"
                "If a poll's message is deleted beforee the poll ends, the poll will be immediately "
                "ended and the results will not be sent. It's like it was never there."
            )
            
        case "chatgpt":
            temp.append(
                f"There are a few ways you can interact with ChatGPT through {interaction.client.user.mention}:\n"
                f"> - **@ mention** Miko in a channel with ChatGPT enabled (change with {mc.tunables('SLASH_COMMAND_SUGGEST_SETTINGS')}) "
                "and type your response. Miko will send your message to ChatGPT and will respond back with ChatGPT's response."
                "\n> \n"
                "> - **Reply** to a message sent by Miko and Miko will respond. Some exceptions: Unreadable embeds or files. You can "
                "also reply to a message not sent by Miko and @ mention Miko and Miko will read the original message."
                "\n> \n"
                "> - **Threads** (private group chat within this server). By default, Miko will determine when to create a thread "
                f"based off of the length of the reply from ChatGPT. This can be changed in {mc.tunables('SLASH_COMMAND_SUGGEST_SETTINGS')}. "
                "In threads, you do not have to mention or reply to Miko to get a response, just type your message and Miko will "
                "respond."
                "\n\n"
                "Miko can also read very long messages (i.e. when you paste in a long message and `message.txt` appears). Miko can read `message.txt` "
                "files and can reply with them just like they are regular messages."
            )

        case _: # No category specified
            temp.append(''.join(await help_embed(mc=mc)))


    

    embed = discord.Embed (
        # title = 'Miko Command List and Brief Description',
        color = mc.tunables('GLOBAL_EMBED_COLOR'),
        description=''.join(temp)
    )
    embed.set_author(icon_url=interaction.client.user.avatar, name=f"{interaction.client.user.name} Help")
    await msg.edit(content=None, embed=embed)



async def help_embed(mc: MikoCore) -> list:
    pr = mc.profile
    temp = []
    temp.append(
        f"{mc.user.client.user.mention} help menu. Use `/help <category>` "
        "for a more detailed explaination. "
        "\n\n"
    )



    if pr.feature_enabled('CHATGPT'):
        temp.append(
            "🌐 __**ChatGPT Integration**__:\n"
            f"> To use ChatGPT, open your settings menu ({mc.tunables('SLASH_COMMAND_SUGGEST_SETTINGS')}) "
            "in the channel you wish to use ChatGPT and select `Channel` -> `ChatGPT Integration`. From here, "
            "you can enable it and set its personality or disable it (per-channel) [must have `Manage Channel` "
            "permission in that channel]."
            "\n> \n"
            "> Once enabled, @ Miko (the bot itself, not the bot role) in the channel you just edited and ask it "
            "anything. You can also reply to Miko to continue the conversation. Note: when replying to Miko you do "
            "not need to @ it. Additionally, if @ing Miko the @ must be the first word in your message."
            "\n\n"
        )



    p = mc.tunables('COMMAND_PREFIX')
    chat_cmds = []
    if pr.cmd_enabled('ROLL') == 1: chat_cmds.append(f"**{p}r**, **{p}roll**: :game_die: Roll a number between 0 and 100\n")
    if pr.cmd_enabled('EIGHT_BALL') == 1: chat_cmds.append(f"**{p}8b**, **{p}8ball**: :8ball: Ask an 8 ball any question\n")
    if pr.cmd_enabled('COIN_FLIP') == 1: chat_cmds.append(f"**{p}fl**, **{p}flip**: :coin: Flip a coin\n")
    if pr.cmd_enabled('ANIME_SEARCH') == 1: chat_cmds.append(f"**{p}as**, **{p}anisearch**: <:uwuyummy:958323925803204618> Search for any anime\n")
    if pr.cmd_enabled('USER_INFO') == 1: chat_cmds.append(f"**{p}s**, **{p}info**: :bar_chart: User Stats/Info\n")
    if len(chat_cmds) > 0:
        temp.append(":speech_balloon: __**Text Commands**__:\n> ")
        temp.append('> '.join(chat_cmds))
        temp.append("\n")

    
    
    slash_cmds = []
    slash_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_HELP')}: :book: Show this help menu\n")
    slash_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_SETTINGS')}: :gear: Change {mc.user.client.user.mention} settings (for yourself and {mc.guild.guild.name})\n")
    if pr.cmd_enabled('PLAYTIME') == 1: slash_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_PLAYTIME')}: :video_game: Playtime tracking and detailed searching\n")
    if pr.cmd_enabled('VOICETIME') == 1: slash_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_VOICETIME')}: :microphone2: Voicechat tracking and detailed searching\n")
    temp.append(":computer: __**Slash Commands**__:\n> ")
    temp.append('> '.join(slash_cmds))



    if pr.cmd_enabled('PLAY') == 1:
        music_cmds = []
        music_cmds.append(
            "Your guild has been granted access music commands and has "
            "access to all features that come with it. This access includes "
            "YouTube. Because of this, this command will remain private and "
            "restricted to limited guilds.\n\n"
        )
        music_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_PLAY')}: :musical_note: Play a song/video from any (soon; YT for now) source.\n")
        music_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_STOP')}: :stop_button: Stops playback and disconnects from voice chat\n")
        music_cmds.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_MUSICCHANNEL')}: :information_source: **Required for all music features**: Set a channel \
                        to be a dedicated music channel. This channel will have a persistent player embed that {mc.user.client.user.mention} \
                        will update. You can skip, pause, stop, control volume, and more with this embed. \
                        Run this command without arguments to deselect the current music channel.\n")
        temp.append("\n:notes: __**Music Player Commands and Info**__:\n")
        temp.append('> '.join(music_cmds))



    # if pr.feature_enabled('THEBOYS_HELP') == 1:
    #     tb = []
    #     tb.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_LEVEL')}: :test_tube: View your level\n")
    #     tb.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_TOKENS')}: :coin: View your tokens `[WIP]`\n")
    #     tb.append(f"{mc.tunables('SLASH_COMMAND_SUGGEST_SHOP')}: :shopping_bags: Token shop `[WIP]`\n")
    #     temp.append(f"\n:gem: __Commands exclusive to **{mc.guild.guild.name}**__:\n> ")
    #     temp.append('> '.join(tb))
        
    return temp