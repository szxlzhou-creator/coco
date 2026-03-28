from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "/",
    response_model=List[AccountResponse],
    summary="List all accounts",
    description="Return every account in the chart of accounts.",
)
def list_accounts(db: Session = Depends(get_db)) -> List[Account]:
    return db.query(Account).order_by(Account.code).all()


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
    description="Add a new account to the chart of accounts.",
)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    existing = db.query(Account).filter(Account.code == payload.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with code '{payload.code}' already exists.",
        )
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Get an account",
    description="Retrieve a single account by its integer ID.",
)
def get_account(account_id: int, db: Session = Depends(get_db)) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return account


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Update an account",
    description="Partially update an account. Only provided fields are changed.",
)
def update_account(
    account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)
) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an account",
    description="Permanently remove an account from the chart of accounts.",
)
def delete_account(account_id: int, db: Session = Depends(get_db)) -> None:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    db.delete(account)
    db.commit()
