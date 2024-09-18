'''
Database file responsible for all database connections
'''

import asyncio
import aiomysql # used for asynchronous database connections
import dns.resolver # used for resolving domain names to IP addresses
import logging
import mysql.connector as mariadb # used ONLY for first time tunables initialization
import os # used for environment variables
import time # for sleep in synchronous database

from dotenv import load_dotenv
load_dotenv()
LOGGER = logging.getLogger()



###########################################################################################################################



LAN_IP = os.getenv('LAN_IP')
VPN_IP = os.getenv('VPN_IP')

_ = [None, ""]
if LAN_IP in _ or VPN_IP in _: LOGGER.critical("IP and/or VPN_IP not set in .env file")

pool = None
async def connect_pool():
    global pool

    # Local database connection
    try:
        LOGGER.debug("Attempting asynchronous database connection via LAN...")
        if os.getenv('CONNECTION') == "REMOTE": raise Exception
        pool = await aiomysql.create_pool(
                host=LAN_IP,
                port=3306,
                connect_timeout=2,
                user=os.getenv('DATABASE_USERNAME'),
                password=os.getenv('DATABASE_PASSWORD'),
                db=os.getenv('DATABASE'),
                loop=asyncio.get_event_loop(),
                autocommit=True
        )
        LOGGER.info("Connected to asynchronous database via LAN!")
    
    # VPN database connection
    except Exception as e:
        LOGGER.debug("Database server not running locally, attempting asynchronous database connection via VPN...")
        try:
            pool = await aiomysql.create_pool(
                    host=VPN_IP,
                    port=3306,
                    user=os.getenv('DATABASE_USERNAME'),
                    password=os.getenv('DATABASE_PASSWORD'),
                    db=os.getenv('DATABASE'),
                    loop=asyncio.get_event_loop(),
                    autocommit=True
            )
            LOGGER.info("Connected to asynchronous database via VPN!")
        except:
            LOGGER.critical(f"Failed to connect to asynchronous database: {e}")

async def check_pool():
    global pool
    if pool is None:
        await connect_pool()
    if pool.closed:
        LOGGER.warning("Asynchronous database connection lost. Attempting to reconnect...")
        await connect_pool()

        
class AsyncDatabase:

    def __init__(self, file):
        self.file = file

    async def execute(self, exec_cmd: str, p=False):
        if p: print(exec_cmd)
        global pool
        for attempt in range(1,6):
            try:
                async with pool.acquire() as conn:
                    cursor = await conn.cursor()
                    await cursor.execute(exec_cmd)
                    conn.close()
            except Exception as e:
                if attempt < 5:
                    if os.getenv('DATABASE_DEBUG') != "1": await asyncio.sleep(5)
                    await check_pool()
                    continue
                else: LOGGER.error(f"ASYNC DATABASE ERROR! [{self.file}] Could not execute: \"{exec_cmd}\"\n{e}")
                raise Exception(f"ASYNC DATABASE ERROR! [{self.file}] Could not execute: \"{exec_cmd}\"\n{e}")
            break
        
        if exec_cmd.startswith("SELECT"):
            val = await cursor.fetchall()
            await cursor.close()
            if len(val) == 1:
                if len(val[0]) == 1:
                    return val[0][0]
            return val if val != () else [] # easier migration from old synchronous code
        await cursor.close()
        return
    
    def exists(self, rows):
        return rows > 0



###########################################################################################################################



'''
Old synchronous database code. Used ONLY for first time tunables initialization
'''

db = None
cur = None
conn = None


def dbclass_connect():
    global db
    global cur

    # Prefer local database connection. Fallback to external Cloudflare
    # connection if local connection is not possible.
    load_dotenv() # Refresh values from .env file (if they changed)
    
    # Local database connection
    try:
        if os.getenv('CONNECTION') == "REMOTE": raise Exception
        LOGGER.debug("[NON-ASYNC] Attempting database connection via LAN...")
        db = mariadb.connect(
            user=os.getenv('DATABASE_USERNAME'),
            password=os.getenv('DATABASE_PASSWORD'),
            host=LAN_IP,
            connect_timeout=2, # Only try for 2 seconds to connect locally.
            port=3306,
            database=os.getenv('DATABASE')
        )
        cur = db.cursor(buffered=True)
        LOGGER.info("[NON-ASYNC] Connected to database via LAN!")
    
    # VPN database connection
    except Exception as e:
        LOGGER.debug("[NON-ASYNC] Database server not running locally, attempting database connection via VPN...")
        try:
            db = mariadb.connect(
                user=os.getenv('DATABASE_USERNAME'),
                password=os.getenv('DATABASE_PASSWORD'),
                host=VPN_IP,
                port=3306,
                database=os.getenv('DATABASE')
            )
            cur = db.cursor(buffered=True)
            LOGGER.info("[NON-ASYNC] Connected to database via VPN!")
        except Exception as e:
            LOGGER.critical(f"[NON-ASYNC] Failed to connect to database: {e}")

    db.autocommit = True
    return

dbclass_connect()

# Function for checking if the database has 1) initially connected,
# 2) is still connected, 3) has disconnected. If the database
# connection has been lost, print message and reconnect
# immediately. Run once for every message sent.
def conn_check():
    if db is None:
        dbclass_connect()
    if not db.is_connected():
        print(f"\n\n####### DATABASE CONNECTION LOST! Attempting to reconnect... #######")
        dbclass_connect()

class Database:
    def __init__(self, name):
        global db
        global cur
        self.db = db
        self.cur = cur
        self.name = name
        #print(f"Database class '{name}' loaded.")
    
    def set_global_vars(self):
        global db
        global cur
        self.db = db
        self.cur = cur
        return

    def db_executor(self, exec_cmd):
        for attempt in range(1,6):
            try:
                self.cur.execute(exec_cmd)
            except mariadb.Error as e:
                if attempt < 5:
                    if os.getenv('DATABASE_DEBUG') != "1": time.sleep(5)
                    conn_check()
                    self.set_global_vars()
                    continue
                else:
                    print(f"\nDATABASE ERROR! [{self.name}] Could not execute: \"{exec_cmd}\"\n{e}")
            break

        if exec_cmd.startswith("SELECT"):
            val = self.cur.fetchall()
            if len(val) == 1:         # Database will return 1 if any information is found.
                if len(val[0]) == 1:  # However, it will error out if we try len(value[0])
                    return val[0][0]  # and there was no information found (the array is
            return val                # not created.)
        return
    
    # Return cursor itself for more advanced cursor operations:
    # fetchone(), fetchmany(#), etc
    def get_cur(self, exec_cmd):
        try:
            self.cur.execute(exec_cmd)
            return self.cur
        except mariadb.Error as e:
            print(f"db_cur error: {e}")
        
        return None
    
    def exists(self, rows):
        if rows > 0:
            return True
        else:
            return False