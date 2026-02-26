import asyncio
from app.services.log_queue import log_queue

class LogBroadcaster:
    def __init__(self):
        self.connections = set()

    async def register(self, websocket):
        self.connections.add(websocket)

    async def unregister(self, websocket):
        self.connections.remove(websocket)

    async def broadcast(self, log):
        if not self.connections:
            return
        
        # Disconnected sockets removal
        to_remove = set()
        for conn in self.connections:
            try:
                await conn.send_json(log)
            except Exception:
                to_remove.add(conn)
        
        for conn in to_remove:
            self.connections.remove(conn)

    async def listen_to_queue(self):
        print("[LogBroadcaster] Started listening to log_queue...")
        while True:
            try:
                message = await log_queue.get()
                await self.broadcast(message)
            except Exception as e:
                print(f"[LogBroadcaster] Error processing message: {e}")

log_broadcaster = LogBroadcaster()
