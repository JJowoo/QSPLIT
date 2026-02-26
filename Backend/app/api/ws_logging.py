from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.log_broadcaster import log_broadcaster
import asyncio

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    await log_broadcaster.register(websocket)
    try:
        while True:
            # Keep the connection open and listen for client messages (optional, or just sleep)
            # If client disconnects, receive_text will raise WebSocketDisconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        await log_broadcaster.unregister(websocket)
        print("[WebSocket] Client disconnected")
    except Exception as e:
        await log_broadcaster.unregister(websocket)
        print(f"[WebSocket] Error: {e}")
