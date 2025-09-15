from fastapi import APIRouter, WebSocket
from app.services.log_queue import log_queue

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await log_queue.get()
            await websocket.send_json(message)
    except Exception as e:
        print(f"[WebSocket] Closed: {e}")
   
