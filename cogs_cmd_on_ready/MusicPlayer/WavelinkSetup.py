import wavelink

from Database.MikoCore import MikoCore
from Database.MySQL import VPN_IP

async def wavelink_setup(client) -> None:
    mc = MikoCore()
    nodes = [wavelink.Node(
        uri=f"http://192.168.0.12:2333",
        password=mc.tunables('WAVELINK_PASSWORD'),
    )]
    
    await wavelink.Pool.connect(nodes=nodes, client=client, cache_capacity=None)




async def on_track_start(payload: wavelink.TrackStartEventPayload) -> None:
    pass