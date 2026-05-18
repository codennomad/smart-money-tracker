from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field


class OptionsFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticker: str
    expiry: date
    strike: float
    callPut: str = Field(validation_alias="call_put")
    premium: float
    volume: int
    openInterest: int = Field(validation_alias="open_interest")
    volOiRatio: float = Field(validation_alias="vol_oi_ratio")
    unusualScore: float = Field(validation_alias="unusual_score")
    detectedAt: datetime = Field(validation_alias="detected_at")


class PaginatedOptions(BaseModel):
    data: list[OptionsFlowOut]
    total: int
    page: int
    pageSize: int
    hasNext: bool
