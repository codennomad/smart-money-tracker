from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models.congress import CongressTrade
from app.schemas.congress import CongressTradeOut, PaginatedCongress

router = APIRouter()


@router.get("", response_model=PaginatedCongress, response_model_by_alias=True)
async def list_congress(
    chamber: str | None = Query(None, pattern=r"^(house|senate)$"),
    party: str | None = Query(None, pattern=r"^(D|R|I)$"),
    ticker: str | None = Query(None, max_length=10, pattern=r"^[A-Z]{1,10}$"),
    page: int = Query(1, ge=1, le=1000),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * pageSize
    filters = []
    if chamber:
        filters.append(CongressTrade.chamber == chamber)
    if party:
        filters.append(CongressTrade.party == party)
    if ticker:
        filters.append(CongressTrade.ticker == ticker)

    stmt = (
        select(CongressTrade)
        .where(and_(*filters))
        .order_by(CongressTrade.disclosed_at.desc())
        .offset(offset)
        .limit(pageSize)
    )
    result = await db.execute(stmt)
    trades = result.scalars().all()

    count_result = await db.execute(select(CongressTrade).where(and_(*filters)))
    total = len(count_result.scalars().all())

    return PaginatedCongress(
        data=trades,
        total=total,
        page=page,
        pageSize=pageSize,
        hasNext=(offset + pageSize) < total,
    )
