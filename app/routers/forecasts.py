from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.forecast import Forecast
from app.schemas.forecast import ForecastCreate, ForecastResponse, ForecastUpdate

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get(
    "/",
    response_model=List[ForecastResponse],
    summary="List forecasts",
    description="Return forecasts. Optionally filter by period and/or account_id.",
)
def list_forecasts(
    period: Optional[str] = Query(default=None, description="Filter by period, e.g. '2024-Q2'"),
    account_id: Optional[int] = Query(default=None, description="Filter by account ID"),
    db: Session = Depends(get_db),
) -> List[Forecast]:
    q = db.query(Forecast)
    if period:
        q = q.filter(Forecast.period == period)
    if account_id is not None:
        q = q.filter(Forecast.account_id == account_id)
    return q.order_by(Forecast.period, Forecast.account_id).all()


@router.post(
    "/",
    response_model=ForecastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a forecast",
    description="Add a forward-looking forecast for an account and period.",
)
def create_forecast(payload: ForecastCreate, db: Session = Depends(get_db)) -> Forecast:
    forecast = Forecast(**payload.model_dump())
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast


@router.get(
    "/{forecast_id}",
    response_model=ForecastResponse,
    summary="Get a forecast",
    description="Retrieve a single forecast by its ID.",
)
def get_forecast(forecast_id: int, db: Session = Depends(get_db)) -> Forecast:
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found.")
    return forecast


@router.put(
    "/{forecast_id}",
    response_model=ForecastResponse,
    summary="Update a forecast",
    description="Partially update a forecast.",
)
def update_forecast(
    forecast_id: int, payload: ForecastUpdate, db: Session = Depends(get_db)
) -> Forecast:
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(forecast, field, value)
    db.commit()
    db.refresh(forecast)
    return forecast


@router.delete(
    "/{forecast_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a forecast",
    description="Permanently remove a forecast.",
)
def delete_forecast(forecast_id: int, db: Session = Depends(get_db)) -> None:
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found.")
    db.delete(forecast)
    db.commit()
