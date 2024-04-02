import discord
from Settings.settings import Setting, tunables


def all_channel_settings(u, p) -> list:
    return [
        ChatGPT(u, p),
        ChatGPTThreads(u, p),
    ]
    
    
class ChatGPT(Setting):

    def __init__(self, u, p):
        super().__init__(
            u=u,
            p=p,
            name = "ChatGPT Integration",
            desc = "Choose to enable ChatGPT Integration and what personality to use",
            emoji = "🌐",
            table = "CHANNELS",
            col = "chatgpt",
            options=tunables('OPENAI_PERSONALITIES')
        )

class ChatGPTThreads(Setting):

    def __init__(self, u, p):
        super().__init__(
            u=u,
            p=p,
            name = "ChatGPT Threads",
            desc = "Create threads (private chat sessions) in this channel when interacting with ChatGPT. Helps prevent clutter.",
            emoji = "🧵",
            table = "CHANNELS",
            col = "chatgpt_threads",
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