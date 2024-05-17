import copy
import discord

from cogs_cmd.Settings.ChannelSettings import all_channel_settings
from cogs_cmd.Settings.GuildSettings import all_guild_settings
from cogs_cmd.Settings.UserSettings import all_user_settings
from cogs_cmd.Settings.settings import Setting
from Database.MikoCore import MikoCore



# Main settings class responsible for entire settings menu interaction
class SettingsView(discord.ui.View):
    def __init__(self, original_interaction: discord.Interaction) -> None:
        self.mc = MikoCore()
        super().__init__(timeout=self.mc.tunables('GLOBAL_VIEW_TIMEOUT'))
        self.original_interaction = original_interaction
        self.scope = {'type': None, 'data': [], 'len': 0}
        self.offset = 0

    @property
    def channel(self) -> discord.TextChannel:
        c = self.original_interaction.channel
        if c.type in self.mc.threads:
            c = c.parent

        return c if self.scope['type'] == "CHANNEL_SETTINGS" else None
    
    @property
    def channel_id(self) -> int:
        if self.channel is None: return None
        return self.channel.id

    async def ainit(self) -> None:
        self.msg = await self.original_interaction.original_response()
        await self.mc.channel_ainit(
            channel=self.original_interaction.channel if self.original_interaction.channel.type not in self.mc.threads else self.original_interaction.channel.parent,
            client=self.original_interaction.client
        )
        await self.main_page()

    async def on_timeout(self) -> None:
        try: await self.msg.delete()
        except: pass

    async def main_page(self) -> None:
        await self.mc.user_ainit(user=self.original_interaction.user, client=self.original_interaction.client)
        
        temp = []
        temp.append(
            f"Most {self.mc.user.client.user.mention} Commands and features can\n"
            "be toggled at any time using this menu."
            "\n\n"
            "__**Select which settings to modify**__:\n\n"
            f"• {self.mc.tunables('SETTINGS_UI_USER_EMOJI')} **Yourself**: Change settings that affect only you (not guild-specific)"
            "\n\n"
            f"• {self.mc.tunables('SETTINGS_UI_CHANNEL_EMOJI')} **Channel**: Change settings that affect this channel\n"
            "Note: Must have `Mange Channel` permission in this channel to modify these settings."
            "\n\n"
            f"• {self.mc.tunables('SETTINGS_UI_GUILD_EMOJI')} **Guild**: Change settings that affect all users in this guild.\n"
            "Note: Must have `Manage Server` permission to modify these settings."
        )
        
        embed = discord.Embed(color=self.mc.tunables('GLOBAL_EMBED_COLOR'), description=''.join(temp))
        embed.set_author(icon_url=self.mc.user.client.user.avatar, name=f"{self.mc.user.client.user.name} Settings")
        
        self.clear_items()
        self.add_item(ChooseScope(miko_user=self.mc.user.client.user.name, mc=self.mc))
        await self.msg.edit(content=None, view=self, embed=embed)

    async def __set_scope(self, interaction: discord.Interaction) -> None:
        self.offset = 0
        match self.scope['type']:
            
            case 'GUILD_SETTINGS':
                if not self.mc.user.manage_guild:
                    await interaction.response.send_message(
                        content=self.mc.tunables('SETTINGS_UI_NO_PERMISSION_GUILD'), ephemeral=True
                    )
                    return
                self.scope['data'] = all_guild_settings(mc=self.mc)
                self.scope['len'] = len(self.scope['data'])
            
            case 'CHANNEL_SETTINGS':
                if not self.mc.user.manage_channel(channel=self.channel):
                    await interaction.response.send_message(
                        content=self.mc.tunables('SETTINGS_UI_NO_PERMISSION_CHANNEL'), ephemeral=True
                    )
                    return
                self.scope['data'] = all_channel_settings(mc=self.mc)
                self.scope['len'] = len(self.scope['data'])
            
            case _:
                self.scope['data'] = all_user_settings(mc=self.mc)
                self.scope['len'] = len(self.scope['data'])

    async def settings_list_page(self, interaction: discord.Interaction, initial=False) -> None:
        if initial: await self.__set_scope(interaction=interaction)
        
        try: await interaction.response.edit_message()
        except: pass
        temp = ["__Select a setting to modify"]
        
        if self.scope['type'] == "CHANNEL_SETTINGS": temp.append(
            f" for {self.channel.mention}__:\n\n"
        )
        else: temp.append("__:\n\n")
        
        for setting in self.scope['data'][self.offset:self.offset+self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE')]:
            setting: Setting
            temp.append(
                "• "
                f"{setting.emoji} "
                f"`{setting.name}`: "
                f"*{setting.desc}*"
                f"{await setting.value_str(channel_id=self.channel_id)}"
                "\n"
            )
        
        embed = discord.Embed(color=self.mc.tunables('GLOBAL_EMBED_COLOR'), description=''.join(temp))
        embed.set_author(
            icon_url=self.mc.user.miko_avatar if self.scope['type'] == "USER_SETTINGS" else self.mc.guild.guild.icon,
            name=f"{self.mc.user.username if self.scope['type'] == 'USER_SETTINGS' else self.mc.guild.guild.name} Settings"
        )
        
        self.clear_items()
        self.add_item(ChooseSetting(settings=self.scope['data'][self.offset:self.offset+self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE')]))
        self.add_item(BackToHome())
        if self.scope['len'] > 5:
            if self.offset > 0:
                self.add_item(PrevButton(disabled=False, mc=self.mc))
            else:
                self.add_item(PrevButton(disabled=True, mc=self.mc))
            if self.scope['len'] > self.offset + self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE') and self.scope['len'] > \
                self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE'):
                    self.add_item(NextButton(disabled=False, mc=self.mc))
            else:
                self.add_item(NextButton(disabled=True, mc=self.mc))
        
        
        await self.msg.edit(content=None, view=self, embed=embed)
        
    async def setting_page(self, s: Setting) -> None:
        
        temp = []
        if self.scope['type'] == "CHANNEL_SETTINGS":
            msg = f" *in* {self.channel.mention}"
        else: msg = ""
        temp.append(
            "• "
            f"{s.emoji} "
            f"`{s.name}`: "
            f"*{s.desc}*{msg}"
            "\n\n"
            "**You currently have this setting set to**:\n"
            f"{await s.value_str(channel_id=self.channel_id)}\n"
            "If you would like to change it, use the dropdown below."
        )
        
        embed = discord.Embed(color=self.mc.tunables('GLOBAL_EMBED_COLOR'), description=''.join(temp), title="You are choosing to modify the following setting:")
        embed.set_author(
            icon_url=self.mc.user.miko_avatar if self.scope['type'] == "USER_SETTINGS" else self.mc.guild.guild.icon,
            name=f"{self.mc.user.username if self.scope['type'] == 'USER_SETTINGS' else self.mc.guild.guild.name} Settings"
        )
        
        # For setting default selected item to
        # item that is set by user
        
        # ChatGPT and other permission-based options are enforced here
        o = copy.deepcopy(s.options)
        permission_level = self.mc.user.bot_permission_level
        x = 0
        options_len = len(o)
        while True:
            if x >= options_len: break
            
            if type(o[x][0]) == int:
                if o[x][0] > permission_level:
                    del o[x]
                    options_len-=1
                    x = 0
                    continue
            
            val = await s.value(self.channel_id)
            if type(val) == bool:
                if val: val = "TRUE"
                else: val = "FALSE"
            if o[x][1].value == val:
                o[x][1].default = True
            else: o[x][1].default = False
            x += 1
        ###
                
        s.options = o
        
        self.clear_items()
        
        self.add_item(ChooseState(setting=s))
        self.add_item(BackToHome())
        await self.msg.edit(content=None, view=self, embed=embed)
    
    async def setting_state_choice(self, interaction: discord.Interaction, s: Setting, choice) -> None:
        mc = MikoCore()
        await mc.user_ainit(user=interaction.user, client=interaction.client)
        check = True
        match self.scope['type']:
            case "CHANNEL_SETTINGS":
                if not mc.user.manage_channel(channel=self.channel): check = False
                msg = self.mc.tunables('SETTINGS_UI_NO_PERMISSION_CHANNEL')
            case "GUILD_SETTINGS":
                if not mc.user.manage_guild: check = False
                msg = self.mc.tunables('SETTINGS_UI_NO_PERMISSION_GUILD')
        
        if not check:
            await interaction.response.send_message(content=msg, ephemeral=True)
            return
    
        await s.set_state(state=choice, channel_id=self.channel_id)
    
        self.clear_items()
        await self.setting_page(s=s)
        await interaction.response.edit_message()
    
    

# Class responsible for listing setting scopes
class ChooseScope(discord.ui.Select):
    def __init__(self, miko_user: str, mc: MikoCore):
        options = [
            discord.SelectOption(
                label="Yourself",
                description=f"Modify your personal {miko_user} settings",
                value="USER_SETTINGS",
                emoji=mc.tunables('SETTINGS_UI_USER_EMOJI')
            ),
            discord.SelectOption(
                label="Channel",
                description=f"Modify {miko_user} settings for this Channel",
                value="CHANNEL_SETTINGS",
                emoji=mc.tunables('SETTINGS_UI_CHANNEL_EMOJI')
            ),
            discord.SelectOption(
                label="Guild",
                description=f"Modify {miko_user} settings for this Guild",
                value="GUILD_SETTINGS",
                emoji=mc.tunables('SETTINGS_UI_GUILD_EMOJI')
            )
        ]
            
        super().__init__(placeholder="Select a category", max_values=1, min_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.scope['type'] = self.values[0]
        await self.view.settings_list_page(interaction=interaction, initial=True)

# Class responsible for listing individual settings
class ChooseSetting(discord.ui.Select):
    def __init__(self, settings: list) -> None:
        options = []
        for i, setting in enumerate(settings):
            setting: Setting
            options.append(
                discord.SelectOption(
                    label=f"{setting.name}",
                    value=i,
                    emoji=setting.emoji
                )
            )
        super().__init__(placeholder="Select a setting", max_values=1, min_values=1, options=options, row=1)
    
    async def callback(self, interaction: discord.Interaction) -> None:
        setting = self.view.scope['data'][int(self.values[0])]
        await interaction.response.edit_message()
        await self.view.setting_page(setting)

class ChooseState(discord.ui.Select):
    def __init__(self, setting: Setting) -> None:
        self.s = setting
        
        # If in guild settings, allow user to change setting for everyone
        # if that setting returns a modifiable value of 3.
        # Else, a value of 3 means the setting is not modifiable for
        # user and channel settings
        #
        # This setting ONLY enforces whether the dropdown box is clickable
        if setting.table == "GUILD_SETTINGS":
            if setting.modifiable['val'] in [1, 3]: disabled = False
            else: disabled = True
        else:
            if setting.modifiable['val'] == 1: disabled = False
            else: disabled = True
            
        super().__init__(
            placeholder="Select an option",
            max_values=1,
            min_values=1,
            options=[option[1] for option in setting.options],
            row=1,
            disabled=disabled
        )
    async def callback(self, interaction: discord.Integration) -> None:
        val = self.values[0]
        await self.view.setting_state_choice(interaction, self.s, val)

# Simple back to home button
class BackToHome(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="Back",
            emoji=None,
            custom_id="back_button",
            row=2
        )
    async def callback(self, interaction: discord.Interaction) -> None:
        try: await interaction.response.edit_message()
        except: pass
        await self.view.main_page()

# Responsible for handling moving back a page
class PrevButton(discord.ui.Button):
    def __init__(self, mc: MikoCore, disabled: bool=False) -> None:
        self.mc = mc
        super().__init__(
            style=discord.ButtonStyle.gray,
            label=None,
            emoji=self.mc.tunables('GENERIC_PREV_BUTTON'),
            custom_id="prev_button",
            row=2,
            disabled=disabled
        )
    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.offset <= self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE'): self.view.offset = 0
        elif self.view.offset > self.view.offset - self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE'): \
            self.view.offset -= self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE')
        else: return
        await self.view.settings_list_page(interaction)
        
# Responsible for handling moving forward a page
class NextButton(discord.ui.Button):
    def __init__(self, mc: MikoCore, disabled: bool=False) -> None:
        self.mc = mc
        super().__init__(
            style=discord.ButtonStyle.gray,
            label=None,
            emoji=self.mc.tunables('GENERIC_NEXT_BUTTON'),
            custom_id="next_button",
            row=2,
            disabled=disabled
        )
    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.scope['len'] > self.view.offset + (self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE') * 2): \
            self.view.offset += self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE')
        elif self.view.scope['len'] <= self.view.offset + (self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE') * 2): \
            self.view.offset = self.view.scope['len'] - self.mc.tunables('SETTINGS_UI_MAX_SETTINGS_LISTABLE')
        else: return
        await self.view.settings_list_page(interaction)
        
