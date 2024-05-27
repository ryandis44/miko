import wavelink

from Database.MikoCore import MikoCore
from Database.MySQL import VPN_IP

async def wavelink_setup(client) -> None:
    mc = MikoCore()