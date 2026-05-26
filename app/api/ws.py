from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.broadcast import add_client, remove_client

router = APIRouter()


@router.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await add_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await remove_client(websocket)
