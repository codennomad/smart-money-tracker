import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OptionsFlow(Base):
    __tablename__ = "options_flow"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    expiry: Mapped[datetime] = mapped_column(Date, nullable=False)
    strike: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    call_put: Mapped[str] = mapped_column(String(4), nullable=False)
    premium: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    open_interest: Mapped[int] = mapped_column(Integer, nullable=False)
    vol_oi_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    unusual_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
