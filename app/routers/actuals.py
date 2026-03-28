from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.actual import Actual
from app.schemas.actual import ActualCreate, ActualResponse, ActualUpdate

router = APIRouter(prefix="/actuals", tags=["Actuals"])


@router.get(
    "/",
    response_model=List[ActualResponse],
    summary="List actual entries",
    description="Return actual financial entries. Optionally filter by period and/or account_id.",
)
def list_actuals(
    period: Optional[str] = Query(default=None, description="Filter by period, e.g. '2024-01'"),
    account_id: Optional[int] = Query(default=None, description="Filter by account ID"),
    db: Session = Depends(get_db),
) -> List[Actual]:
    q = db.query(Actual)
    if period:
        q = q.filter(Actual.period == period)
    if account_id is not None:
        q = q.filter(Actual.account_id == account_id)
    return q.order_by(Actual.period, Actual.account_id).all()


@router.post(
    "/",
    response_model=ActualResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an actual entry",
    description="Record a new actual financial transaction or journal entry.",
)
def create_actual(payload: ActualCreate, db: Session = Depends(get_db)) -> Actual:
    actual = Actual(**payload.model_dump())
    db.add(actual)
    db.commit()
    db.refresh(actual)
    return actual


@router.get(
    "/{actual_id}",
    response_model=ActualResponse,
    summary="Get an actual entry",
    description="Retrieve a single actual entry by its ID.",
)
def get_actual(actual_id: int, db: Session = Depends(get_db)) -> Actual:
    actual = db.query(Actual).filter(Actual.id == actual_id).first()
    if not actual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual entry not found.")
    return actual


@router.put(
    "/{actual_id}",
    response_model=ActualResponse,
    summary="Update an actual entry",
    description="Partially update an actual entry.",
)
def update_actual(
    actual_id: int, payload: ActualUpdate, db: Session = Depends(get_db)
) -> Actual:
    actual = db.query(Actual).filter(Actual.id == actual_id).first()
    if not actual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual entry not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(actual, field, value)
    db.commit()
    db.refresh(actual)
    return actual


@router.delete(
    "/{actual_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an actual entry",
    description="Permanently remove an actual entry.",
)
def delete_actual(actual_id: int, db: Session = Depends(get_db)) -> None:
    actual = db.query(Actual).filter(Actual.id == actual_id).first()
    if not actual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual entry not found.")
    db.delete(actual)
    db.commit()
