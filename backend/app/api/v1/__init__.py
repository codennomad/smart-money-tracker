from fastapi import APIRouter
from .routes import insiders, congress, options, darkpool, alerts, ws

router = APIRouter()
router.include_router(insiders.router, prefix="/insiders", tags=["insiders"])
router.include_router(congress.router, prefix="/congress", tags=["congress"])
router.include_router(options.router, prefix="/options", tags=["options"])
router.include_router(darkpool.router, prefix="/darkpool", tags=["darkpool"])
router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
router.include_router(ws.router, prefix="/ws", tags=["websocket"])
