from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AnomalyAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticker: str
    alertType: str = Field(validation_alias="alert_type")
    confidence: float
    description: str
    relatedIds: list[str] = Field(validation_alias="related_ids")
    detectedAt: datetime = Field(validation_alias="detected_at")
