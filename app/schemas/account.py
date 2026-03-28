from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

AccountType = Literal["revenue", "expense", "asset", "liability", "equity"]


class AccountBase(BaseModel):
    code: str
    name: str
    type: AccountType
    description: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    type: Optional[AccountType] = None
    description: Optional[str] = None


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
