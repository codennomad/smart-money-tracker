import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CongressTrade(Base):
    __tablename__ = "congress_trades"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    member: Mapped[str] = mapped_column(String(200), nullable=False)
    party: Mapped[str] = mapped_column(String(1), nullable=False)
    chamber: Mapped[str] = mapped_column(String(10), nullable=False)
    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_min: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    amount_max: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    disclosed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    days_to_disclose: Mapped[int] = mapped_column(Integer, nullable=False)
