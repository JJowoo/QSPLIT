import asyncio

class LogBroadcaster:
    def __init__(self):
        self.connections = set()

    async def register(self, websocket):
        self.connections.add(websocket)

    async def unregister(self, websocket):
        self.connections.remove(websocket)

    async def broadcast(self, log):
        for conn in list(self.connections):
            try:
                await conn.send_json(log)
            except:
                await self.unregister(conn)

log_broadcaster = LogBroadcaster()
