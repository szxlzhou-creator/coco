from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActualBase(BaseModel):
    account_id: int
    period: str
    amount: float
    description: Optional[str] = None
    transaction_date: date


class ActualCreate(ActualBase):
    pass


class ActualUpdate(BaseModel):
    account_id: Optional[int] = None
    period: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None


class ActualResponse(ActualBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
