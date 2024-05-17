'''
(insert how this works here)
'''



from cogs_cmd.Settings.settings import Setting

def all_guild_settings(mc) -> list:
    return [
        BigEmojisGuild(mc),
        NickInCtx(mc),
        GreetNewMembers(mc),
        NotifyMemberLeave(mc),
        BruhReact(mc),
    ]

class BigEmojisGuild(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Guild Big Emojis",
            desc = "Enlarge custom emojis for a better viewing experience (only works on non-default emojis)",
            emoji = "😂",
            table = "GUILD_SETTINGS",
            col = "big_emojis"
        )

class NickInCtx(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Guild Nicknames in Context",
            desc = "Whether or not to use nicknames when referencing users in embeds",
            emoji = "✏",
            table = "GUILD_SETTINGS",
            col = "nickname_in_ctx"
        )

class GreetNewMembers(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Greet new members",
            desc = "Send a message to the system channel welcoming new members",
            emoji = "👋",
            table = "GUILD_SETTINGS",
            col = "greet_new_members"
        )

class NotifyMemberLeave(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Member leave messages",
            desc = "Send a message to system channel when a member leaves the server",
            emoji = "✌",
            table = "GUILD_SETTINGS",
            col = "notify_member_leave"
        )

class BruhReact(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Bruh React",
            desc = "React with 'B R U H' when certain words are mentioned in chat",
            emoji = "🫱",
            table = "GUILD_SETTINGS",
            col = "bruh_react"
        )