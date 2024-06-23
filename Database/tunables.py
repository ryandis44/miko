'''
This file is responsible for handling tunables, which are variables that can be changed without needing to restart the bot
These tunables are stored in a database table, and are loaded into memory when the bot starts up
The tunables can be refreshed at any time, and the bot will automatically update the values in memory
The tunables are used to configure the bot's behavior, and can be used to enable or disable certain features
The tunables are also used to store information about guild profiles, which are used to configure the bot's behavior on a per-guild basis
The tunables are stored in a dictionary, with the variable name as the key, and the value as the value
'''



import logging

from Database.MySQL import Database, AsyncDatabase
from discord import ButtonStyle, ChannelType, Color, SelectOption
from json import loads
db = AsyncDatabase(__file__)
LOGGER = logging.getLogger()

THREAD_TYPES = [ChannelType.public_thread, ChannelType.private_thread, ChannelType.news_thread]

TUNABLES = {}
def tunables(s):
    try: return TUNABLES[s]
    except Exception as e:
        LOGGER.error(f"TUNABLES ERROR: Could not find '{s}' | {e}")
        return None

def all_tunable_keys() -> list: return [*TUNABLES]

def tunables_init(): # Initial call cannot be async
    assign_tunables(
        val=Database("TUNABLES INITIALIZATION").db_executor(
            "SELECT * FROM TUNABLES "
            "ORDER BY variable ASC"
        )
    )

async def tunables_refresh():
    assign_tunables(await db.execute(
        "SELECT * FROM TUNABLES "
        "ORDER BY variable ASC"
    ))

def assign_tunables(val):
    global TUNABLES
    TUNABLES = {}
    for tunable in val:
        try:
            if tunable[1] == "TRUE": TUNABLES[tunable[0]] = True
            if tunable[1] == "FALSE": TUNABLES[tunable[0]] = False
            if tunable[1][0:2] == "0x": TUNABLES[tunable[0]] = int(tunable[1], 16)
            elif tunable[1] not in ["TRUE", "FALSE"]:
                if tunable[1] is not None and tunable[1].isdigit(): TUNABLES[tunable[0]] = int(tunable[1])
                else: TUNABLES[tunable[0]] = tunable[1]
        except Exception as e: LOGGER.error(f"TUNABLES ERROR: (({e})) Could not ASSIGN: {tunable}")
    configure_tunables()

def configure_tunables() -> None:
    global TUNABLES
    TUNABLES['GENERATIVE_AI_MODES'] = []
    temp = []
    for key, val in TUNABLES.items():
        try:
            if 'PERMS_PROFILE_' in key:
                TUNABLES[key] = PermissionProfile(profile=str(key)[14:])
            
            if 'GENERATIVE_AI_MODE_' in key:
                d = loads(val)
                temp.append(d)
        except Exception as e: LOGGER.error(f"TUNABLES ERROR: (({e})) Could not CONFIGURE PROFILE {key} {val}")
    
    def srt(d) -> int:
        return d['position']
    try: temp.sort(key=srt)
    except Exception as e: LOGGER.error(f"TUNABLES ERROR: Could not SORT AI PERSONALITIES: {e}")
    for d in temp:
        try:
            TUNABLES['GENERATIVE_AI_MODES'].append(
                [
                    int(d['permission_level']),
                    SelectOption(
                        label=d['label'],
                        description=d['description'],
                        value=d['value'],
                        emoji=d['emoji']
                    )
                ]
            )
            TUNABLES[f"GENERATIVE_AI_MODE_{d['value']}"] = {
                'prompt': d['prompt'],
                'model': d['model'],
                'api': d['api'],
                'value': d['value'],
                'input_tokens': d['input_tokens'],
                'response_tokens': d['response_tokens']
            }
        except Exception as e:
            try:
                TUNABLES['GENERATIVE_AI_MODES'].pop()
                del TUNABLES[f"GENERATIVE_AI_MODE_{d['value']}"]
            except: pass
            LOGGER.error(f"TUNABLES ERROR: (({e})) Could not CONFIGURE PERSONALITY: {d}")





class PermissionProfile():

    def __init__(self, profile: str):
        self.params = str(tunables(f'PERMS_PROFILE_{profile}')).split(',')
        self.profile = profile
        self.v = {}
        
        self.__commands = {'all_enabled': False, 'inverse': False}
        self.__features = {'all_enabled': False, 'inverse': False}
        self.__handle_params()



    def __str__(self):
        return f"{self.profile} | {self.params}"
    
    
    
    def inject_guild(self, guild_settings: dict) -> None: self.__guild_settings = guild_settings
    
    
    
    def __handle_params(self) -> None:
        for option in self.params:
            option = option.split("[")
            option[1] = option[1].replace("]", "")
            
            if option[0].startswith("!"):
                option[0] = option[0].replace("!", "")
                inverse = True
            else: inverse = False
            
            match option[0]:
                
                case "COMMANDS":
                    self.__commands['inverse'] = inverse
                    if option[1] in ["ALL"]:
                        self.__commands['all_enabled'] = True
                        continue
                    prefix = "C"
                    
                case "FEATURES":
                    self.__features['inverse'] = inverse
                    if option[1] in ["ALL"]:
                        self.__features['all_enabled'] = True
                        continue
                    prefix = "F"
                
                case _: prefix = None


            option = str(option[1]).split(";")
            for cmd in option:
                self.v[f'{prefix}_{cmd.upper()}'] = not inverse
            
    
    
    # For the following two functions, return values mean:
    # - 0: Guild profile does not have command enabled
    # - 1: Guild profile and tunables have command enabled
    # - 2: Tunables does not have command enabled
    # - 3: Guild owner does not have command enabled
    
    def cmd_enabled(self, cmd: str) -> int:
        if not tunables(f'COMMAND_ENABLED_{cmd.upper()}'): return 2
        if self.__guild_settings.get(cmd.lower()) == False: return 3
        if self.__commands['all_enabled']:
            if self.__commands['inverse']: return 0
            return 1
        
        try: val = self.v[f"C_{cmd}"]
        except: val = None
        if val is None: val = self.__commands['inverse']
        return 1 if val else 0
    
    def feature_enabled(self, f: str) -> int:
        if not tunables(f'FEATURE_ENABLED_{f.upper()}'): return 2
        if self.__guild_settings.get(f.lower()) == False: return 3
        if self.__features['all_enabled']:
            if self.__features['inverse']: return 0
            return 1
        
        try: val = self.v[f"F_{f}"]
        except: val = None
        if val is None: val = self.__features['inverse']
        return 1 if val else 0