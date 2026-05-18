import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DarkPoolPrint(Base):
    __tablename__ = "darkpool_prints"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    short_volume: Mapped[int] = mapped_column(Integer, nullable=False)
    short_exempt_volume: Mapped[int] = mapped_column(Integer, nullable=False)
    total_volume: Mapped[int] = mapped_column(Integer, nullable=False)
    short_pct: Mapped[float] = mapped_column(Float, nullable=False)
    report_date: Mapped[datetime] = mapped_column(Date, index=True, nullable=False)
