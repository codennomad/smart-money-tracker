from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CongressTradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    member: str
    party: str
    chamber: str
    ticker: str
    company: str | None
    transactionType: str = Field(validation_alias="transaction_type")
    amountMin: float = Field(validation_alias="amount_min")
    amountMax: float = Field(validation_alias="amount_max")
    transactionDate: datetime = Field(validation_alias="transaction_date")
    disclosedAt: datetime = Field(validation_alias="disclosed_at")
    daysToDisclose: int = Field(validation_alias="days_to_disclose")


class PaginatedCongress(BaseModel):
    data: list[CongressTradeOut]
    total: int
    page: int
    pageSize: int
    hasNext: bool
