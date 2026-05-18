from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.config import get_settings
from app.models.insider import InsiderTrade
from app.schemas.insider import InsiderTradeOut, PaginatedInsiders

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.get("", response_model=PaginatedInsiders, response_model_by_alias=True)
async def list_insiders(
    ticker: str | None = Query(None, max_length=10, pattern=r"^[A-Z]{1,10}$"),
    type: str | None = Query(None, pattern=r"^(buy|sell)$"),
    page: int = Query(1, ge=1, le=1000),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * pageSize
    filters = []
    if ticker:
        filters.append(InsiderTrade.ticker == ticker)
    if type:
        filters.append(InsiderTrade.transaction_type == type)

    stmt = (
        select(InsiderTrade)
        .where(and_(*filters))
        .order_by(InsiderTrade.filed_at.desc())
        .offset(offset)
        .limit(pageSize)
    )
    result = await db.execute(stmt)
    trades = result.scalars().all()

    count_stmt = select(InsiderTrade).where(and_(*filters))
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return PaginatedInsiders(
        data=trades,
        total=total,
        page=page,
        pageSize=pageSize,
        hasNext=(offset + pageSize) < total,
    )
