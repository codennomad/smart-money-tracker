from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.alert import AnomalyAlert
from app.schemas.alert import AnomalyAlertOut

router = APIRouter()


@router.get("", response_model=list[AnomalyAlertOut], response_model_by_alias=True)
async def list_alerts(db: AsyncSession = Depends(get_db)):
    stmt = select(AnomalyAlert).order_by(AnomalyAlert.detected_at.desc()).limit(20)
    result = await db.execute(stmt)
    return result.scalars().all()
