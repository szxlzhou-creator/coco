from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get(
    "/",
    response_model=List[BudgetResponse],
    summary="List budgets",
    description="Return budget line items. Optionally filter by period and/or account_id.",
)
def list_budgets(
    period: Optional[str] = Query(default=None, description="Filter by period, e.g. '2024-Q1'"),
    account_id: Optional[int] = Query(default=None, description="Filter by account ID"),
    db: Session = Depends(get_db),
) -> List[Budget]:
    q = db.query(Budget)
    if period:
        q = q.filter(Budget.period == period)
    if account_id is not None:
        q = q.filter(Budget.account_id == account_id)
    return q.order_by(Budget.period, Budget.account_id).all()


@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budget entry",
    description="Add a new budget line item for an account and period.",
)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db)) -> Budget:
    budget = Budget(**payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Get a budget entry",
    description="Retrieve a single budget line item by its ID.",
)
def get_budget(budget_id: int, db: Session = Depends(get_db)) -> Budget:
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    return budget


@router.put(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update a budget entry",
    description="Partially update a budget line item.",
)
def update_budget(
    budget_id: int, payload: BudgetUpdate, db: Session = Depends(get_db)
) -> Budget:
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget entry",
    description="Permanently remove a budget line item.",
)
def delete_budget(budget_id: int, db: Session = Depends(get_db)) -> None:
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    db.delete(budget)
    db.commit()
