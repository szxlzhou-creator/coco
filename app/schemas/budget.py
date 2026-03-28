from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BudgetBase(BaseModel):
    account_id: int
    period: str
    amount: float
    notes: Optional[str] = None


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    account_id: Optional[int] = None
    period: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None


class BudgetResponse(BudgetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
