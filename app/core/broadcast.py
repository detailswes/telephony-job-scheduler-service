import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)

connected_clients: set[WebSocket] = set()
_clients_lock = asyncio.Lock()


async def add_client(websocket: WebSocket) -> None:
    async with _clients_lock:
        connected_clients.add(websocket)


async def remove_client(websocket: WebSocket) -> None:
    async with _clients_lock:
        connected_clients.discard(websocket)


async def broadcast(message: str) -> None:
    async with _clients_lock:
        clients = list(connected_clients)

    dead: set[WebSocket] = set()
    for client in clients:
        try:
            await client.send_text(message)
        except Exception:
            dead.add(client)

    if dead:
        async with _clients_lock:
            connected_clients.difference_update(dead)
