import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class InsiderTrade(Base):
    __tablename__ = "insider_trades"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    insider_name: Mapped[str] = mapped_column(String(200), nullable=False)
    insider_title: Mapped[str] = mapped_column(String(200), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    shares: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_share: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    filed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(20), default="form4")
    form_url: Mapped[str] = mapped_column(String(500), nullable=True)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=True)
