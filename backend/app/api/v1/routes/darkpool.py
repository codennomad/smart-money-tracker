from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.darkpool import DarkPoolPrint
from app.schemas.darkpool import DarkPoolPrintOut, PaginatedDarkPool

router = APIRouter()


@router.get("", response_model=PaginatedDarkPool, response_model_by_alias=True)
async def list_darkpool(
    ticker: str | None = Query(None, max_length=10, pattern=r"^[A-Z]{1,10}$"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DarkPoolPrint).order_by(DarkPoolPrint.report_date.desc()).limit(100)
    if ticker:
        stmt = stmt.where(DarkPoolPrint.ticker == ticker)
    result = await db.execute(stmt)
    prints = result.scalars().all()
    return PaginatedDarkPool(data=prints, total=len(prints), page=1, pageSize=100, hasNext=False)
