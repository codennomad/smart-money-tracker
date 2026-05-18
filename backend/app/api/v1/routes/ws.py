"""
WebSocket feed — broadcasts anomaly alerts to connected clients.
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

_connections: set[WebSocket] = set()


@router.websocket("/feed")
async def ws_feed(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            # Keep-alive ping every 30s
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(websocket)


async def broadcast(payload: dict) -> None:
    dead: set[WebSocket] = set()
    for ws in _connections:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)
