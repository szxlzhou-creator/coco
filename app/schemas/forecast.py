from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ForecastMethod = Literal["manual", "linear_trend", "moving_average"]


class ForecastBase(BaseModel):
    account_id: int
    period: str
    amount: float
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    method: ForecastMethod = "manual"
    notes: Optional[str] = None


class ForecastCreate(ForecastBase):
    pass


class ForecastUpdate(BaseModel):
    account_id: Optional[int] = None
    period: Optional[str] = None
    amount: Optional[float] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    method: Optional[ForecastMethod] = None
    notes: Optional[str] = None


class ForecastResponse(ForecastBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
