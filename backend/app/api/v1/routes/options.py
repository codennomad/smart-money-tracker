from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.options import OptionsFlow
from app.schemas.options import OptionsFlowOut, PaginatedOptions

router = APIRouter()


@router.get("/unusual", response_model=PaginatedOptions, response_model_by_alias=True)
async def unusual_options(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(OptionsFlow)
        .where(OptionsFlow.unusual_score >= 0.7)
        .order_by(OptionsFlow.detected_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    flows = result.scalars().all()
    return PaginatedOptions(data=flows, total=len(flows), page=1, pageSize=50, hasNext=False)
