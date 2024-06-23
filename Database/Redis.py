'''
Redis is a key-value store that is used to cache messages
'''

import asyncio
import logging
import os
import redis.asyncio as redis

from Database.MySQL import IP, AsyncDatabase
from Database.tunables import tunables
from redis.commands.json.path import Path
from redis.commands.search.query import Query
db = AsyncDatabase('Database.RedisCache.py')
LOGGER = logging.getLogger()

connection = None
async def connect_redis():
    global connection
    
    try:
        LOGGER.debug("Attempting connection to Redis server...")
        if os.getenv('CONNECTION') == "REMOTE": raise Exception
        connection = redis.Redis(
            host='192.168.0.12',
            port=tunables('REDIS_PORT'),
            password=tunables('REDIS_PASSWORD'),
            decode_responses=True,
            socket_timeout=2
        )
        if not await connection.ping(): raise Exception
        
        LOGGER.info("Connected to Redis server via LAN!")
    except Exception as e:
        LOGGER.debug("Redis server not running locally, attempting connection via Cloudflare...")
        try:
            connection = redis.Redis(
                host=IP,
                port=tunables('REDIS_PORT'),
                password=tunables('REDIS_PASSWORD'),
                decode_responses=True
            )
            
            if not await connection.ping(): raise Exception
            
            LOGGER.info("Connected to Redis server via Cloudflare!\n")
        except:
            LOGGER.critical(f"Failed to connect to Redis server: {e}")


async def check_redis():
    global connection
    if connection is None:
        await connect_redis()
    try:
        if not await connection.ping(): raise Exception
    except: await connect_redis()

class RedisCache:
    
    def __init__(self, file):
        self.file = file
    
    async def set(self, key: str, value, type: str, path: str=".", p=False) -> bool:
        if p: print(
            f"> Key: {key}\n"
            f"> Value: {value}"
        )
        global connection
        for attempt in range(1,6):
            try:
                async with connection.pipeline(transaction=True) as pipe:
                    match type:
                        case "STRING": pipe.set(key, value)
                        case "JSON": pipe.json().set(key, path, value)
                    pipe.expire(key, tunables('REDIS_KEY_EXPIRE'))
                    await pipe.execute()
            except Exception as e:
                if attempt < 5:
                    if os.getenv('DATABASE_DEBUG') != "1": await asyncio.sleep(5)
                    await check_redis()
                    continue
                else:
                    LOGGER.error(f"\n[REDIS] ERROR! [{self.file}] Could not SET VALUE: \"{key, value}\"\n{e}")
                    return False
            return True
    
    
    
    async def get(self, key: str, type: str) -> dict|str|None:
        global connection
        # async with connection.pipeline(transaction=True) as pipe:
        try:
            match type:
                case "STRING": return await connection.get(key)
                case "JSON": return await connection.json().get(key)
        except: return None

    async def search(self, query: str, type: str, index: str, offset: int = 0, limit: int = 10) -> dict|list|str|None:
        try:
            match type:
                case "STRING": ...
                case "JSON_THREAD_ID":
                    q = Query(query)
                    q.paging(offset, limit)
                    q.sort_by(field="created_at", asc=False)
                    return (await connection.ft(index_name=index).search(q)).docs
        except Exception as e:
            LOGGER.error(f"\n[REDIS] ERROR! [{self.file}] Could not SEARCH BY QUERY: \"{query}\"\n{e}")
            return None
    
    async def delete(self, key: str) -> None:
        global connection
        try: await connection.delete(key)
        except: pass