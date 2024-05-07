'''
Miko! Discord bot main file. This file is responsible for starting the bot, and loading all the necessary libraries and files.
Any extra features are referenced by main.py, and are imported as needed. No core functionality is implemented in this file.
'''

import asyncio
import discord
import logging # used for logging messages to the console and log file
import os # used for exiting the program without error messages
import signal # used for handling shutdown signals (ctrl+c)

from discord.ext import commands
from dotenv import load_dotenv # load environment variables from .env file
from dpyConsole import Console # console used for debugging, logging, and shutdown via control panel
from tunables import tunables_init, tunables # tunables used by the bot



###########################################################################################################################



'''
Set up logger and load variables
'''

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
handler = logging.FileHandler(filename='miko.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)s: %(message)s'))
LOGGER.addHandler(handler)

tunables_init()
load_dotenv() # load environment variables from .env file



###########################################################################################################################



'''
Define bot intents. These are used to determine what events the bot will receive.
'''

intents = discord.Intents.all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix=tunables("COMMAND_PREFIX"), intents=intents, case_insensitive=True, help_command=None)
console = Console(client=client)



###########################################################################################################################



'''
Handle shutdown signal from keyboard and console.
'''

def thread_kill(one=None, two=None):
    print("Shutting down...")
    LOGGER.log(level=logging.CRITICAL, msg="Shutting down...")
    print("Graceful shutdown complete. Goodbye.")
    LOGGER.log(level=logging.CRITICAL, msg="Graceful shutdown complete. Goodbye.")
    os._exit(0)
signal.signal(signal.SIGINT, thread_kill)

@console.command()
async def shutdown(): thread_kill()



###########################################################################################################################



'''
Load all cogs from the cogs directories
'''

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')
            LOGGER.log(level=logging.DEBUG, msg=f'Loaded cog: {filename[:-3]}')
    LOGGER.log(level=logging.DEBUG, msg='All cogs loaded.')

async def load_cogs_console():
    for filename in os.listdir('./cogs_console'):
        if filename.endswith('.py'):
            console.load_extension(f'cogs.{filename[:-3]}')
            LOGGER.log(level=logging.DEBUG, msg=f'Loaded console cog: {filename[:-3]}')
    LOGGER.log(level=logging.DEBUG, msg='All console cogs loaded.')



###########################################################################################################################



'''
Start the bot
'''

async def main() -> None:
    async with client:
        await load_cogs()
        # console.start()
        # await load_cogs_console()
        await client.start(os.getenv('DISCORD_TOKEN'))

@client.event
async def on_ready() -> None:
    LOGGER.log(level=logging.INFO, msg=f'Logged in as {client.user} {client.user.id}')
    print('bot online') # for pterodactyl console for online status

asyncio.run(main())