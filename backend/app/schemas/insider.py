from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InsiderTradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticker: str
    company: str
    insiderName: str = Field(validation_alias="insider_name")
    insiderTitle: str | None = Field(None, validation_alias="insider_title")
    transactionType: str = Field(validation_alias="transaction_type")
    shares: int
    pricePerShare: float = Field(validation_alias="price_per_share")
    totalValue: float = Field(validation_alias="total_value")
    filedAt: datetime = Field(validation_alias="filed_at")
    transactionDate: datetime = Field(validation_alias="transaction_date")
    source: str
    formUrl: str | None = Field(None, validation_alias="form_url")
    anomalyScore: float | None = Field(None, validation_alias="anomaly_score")


class PaginatedInsiders(BaseModel):
    data: list[InsiderTradeOut]
    total: int
    page: int
    pageSize: int
    hasNext: bool
