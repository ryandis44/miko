import discord

from cogs_cmd.Settings.settings import Setting
from Database.tunables import tunables


def all_channel_settings(mc) -> list:
    return [
        TextAI(mc),
        TextAIThreads(mc),
    ]
    
    
class TextAI(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Generative Text AI Integration",
            desc = "Choose to enable Generative Text AI Integration and what personality to use",
            emoji = "🌐",
            table = "CHANNEL_SETTINGS",
            col = "text_ai_mode",
            options=tunables('OPENAI_PERSONALITIES')
        )

class TextAIThreads(Setting):

    def __init__(self, mc):
        super().__init__(
            mc=mc,
            name = "Generative Text AI Threads",
            desc = "Create threads (private chat sessions) in this channel when interacting with Generative Text AI. Helps prevent clutter.",
            emoji = "🧵",
            table = "CHANNEL_SETTINGS",
            col = "text_ai_threads",
            options=[
                [
                    1,
                    discord.SelectOption(
                        label=f"Enabled: Always",
                        description=f"Create a thread for every response.",
                        value="ALWAYS",
                        emoji="🟢"
                    )
                ],
                [
                    1,
                    discord.SelectOption(
                        label=f"Enabled: Auto (default)",
                        description=f"Let Miko decide when to create a thread.",
                        value="AUTO",
                        emoji="🤖"
                    )
                ],
                [
                    0,
                    discord.SelectOption(
                        label=f"Disabled",
                        description=f"Always respond in this channel.",
                        value="DISABLED",
                        emoji="❌"
                    )
                ]
            ]
        )