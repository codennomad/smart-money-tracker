from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class DarkPoolPrintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticker: str
    shares: int
    price: float
    totalValue: float = Field(validation_alias="total_value")
    shortVolume: int = Field(validation_alias="short_volume")
    shortExemptVolume: int = Field(validation_alias="short_exempt_volume")
    totalVolume: int = Field(validation_alias="total_volume")
    shortPct: float = Field(validation_alias="short_pct")
    reportDate: date = Field(validation_alias="report_date")


class PaginatedDarkPool(BaseModel):
    data: list[DarkPoolPrintOut]
    total: int
    page: int
    pageSize: int
    hasNext: bool
