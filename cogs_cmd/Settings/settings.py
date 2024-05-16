'''

'''



import discord

from Database.MikoCore import MikoCore
from Database.MySQL import AsyncDatabase
db = AsyncDatabase(__file__)

class Setting:

    def __init__(self,
        mc: MikoCore,
        name: str,
        desc: str,
        emoji: str,
        table: str,
        col: str,
        options: list[int, discord.SelectOption] = None
    ) -> None:

        self.mc = mc
        self.name = name
        self.desc = desc
        self.emoji = emoji
        self.table = table
        self.col = col
        self.permission_level = 1
        self.modifiable = mc.profile.feature_enabled(f'{col.upper()}')
        self.modifiable = {
            'val': self.modifiable,
            'reason': \
                "- Not enabled in this guild -"\
                    if self.modifiable == 0 else \
                        "- Temporarily disabled in all guilds -" \
                            if self.modifiable == 2 else \
                                "- Disabled by guild admin -"
        }
        
        if options is not None: self.options = options
        else:
            match self.table:
                case 'CHANNEL_SETTINGS': ctx = "in this channel."
                case 'GUILD_SETTINGS': ctx = "in this guild."
                case _: ctx = "for yourself."
            
            self.options = [
                [
                    self.permission_level,
                    discord.SelectOption(
                        label=f"Enable {self.name}",
                        description=f"Select to enable {self.name} {ctx}",
                        value="TRUE",
                        emoji="☑"
                    )
                ],
                [
                    0,
                    discord.SelectOption(
                        label=f"Disable {self.name}",
                        description=f"Select to disable {self.name} {ctx}",
                        value="FALSE",
                        emoji="❌"
                    )
                ]
            ]
    
    
    def __str__(self): return f"{self.name} Settings Object"



    async def value(self, channel_id=None):
        match self.table:
            case 'CHANNEL_SETTINGS': scope = f"channel_id='{channel_id}'"
            case 'GUILD_SETTINGS': scope = f"guild_id='{self.mc.guild.guild.id}'"
            case _: scope = f"user_id='{self.mc.user.user.id}'"
            
        val = await db.execute(
            f"SELECT {self.col} FROM {self.table} WHERE "
            f"{scope} LIMIT 1"
        )
        if val == "FALSE": return False
        elif val == "TRUE": return True
        return val
    
    
    
    async def value_str(self, channel_id=None):
        val = await self.value(channel_id=channel_id)
        if type(val) == bool:
            if val: state = "+ ENABLED +"
            else: state = "- DISABLED -"
        else:
            val = val.upper()
            if val == "DISABLED": state = "- DISABLED -"
            else: state = f"+ {val} +"
        
        reason = ""
        if self.table == "GUILD_SETTINGS":
            if self.modifiable['val'] not in [1,3]:
                state = "- DISABLED -"
                reason = self.modifiable['reason']
        else:
            if self.modifiable['val'] not in [1]:
                state = "- DISABLED -"
                reason = self.modifiable['reason']
        
        return (
            "```diff\n"
            f"{state}\n"
            f"{reason}"
            "```"
        )
    
    

    async def set_state(self, state=None, channel_id=None) -> str:
        val = await self.value(channel_id=channel_id)
        
        match self.table:
            case 'CHANNEL_SETTINGS': scope = f"channel_id='{channel_id}'"
            case 'GUILD_SETTINGS': scope = f"guild_id='{self.mc.guild.guild.id}'"
            case _: scope = f"user_id='{self.mc.user.user.id}'"
        
        # If state is None, then val must be bool. Set to opposite.
        if state is None: state = 'TRUE' if val else 'FALSE'
        
        await db.execute(
            f"UPDATE {self.table} SET {self.col}='{state}' WHERE "
            f"{scope}"
        )
        return state