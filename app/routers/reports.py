"""
Reports router — all read-only analytics endpoints.

Each query joins the relevant data tables with the accounts table so the
analytics service receives denormalised row objects via SimpleNamespace,
keeping the service layer free of SQLAlchemy dependencies.
"""

from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.models.actual import Actual
from app.models.budget import Budget
from app.models.forecast import Forecast
from app.schemas.report import (
    CashFlowSummary,
    ForecastAccuracyReport,
    PeriodSummary,
    VarianceReport,
)
from app.services.analytics import (
    compute_cash_flow,
    compute_forecast_accuracy,
    compute_period_summary,
    compute_variance,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


def _budget_rows(db: Session, period: Optional[str]) -> List[SimpleNamespace]:
    """Return budget rows joined with account data."""
    q = (
        db.query(
            Budget.period,
            Budget.account_id,
            Budget.amount.label("budget_amount"),
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            Account.type.label("account_type"),
        )
        .join(Account, Budget.account_id == Account.id)
    )
    if period:
        q = q.filter(Budget.period == period)
    return [SimpleNamespace(**dict(row._mapping)) for row in q.all()]


def _actual_rows(db: Session, period: Optional[str]) -> List[SimpleNamespace]:
    """Return actual rows joined with account data."""
    q = (
        db.query(
            Actual.period,
            Actual.account_id,
            Actual.amount,
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            Account.type.label("account_type"),
        )
        .join(Account, Actual.account_id == Account.id)
    )
    if period:
        q = q.filter(Actual.period == period)
    return [SimpleNamespace(**dict(row._mapping)) for row in q.all()]


def _forecast_rows(db: Session, period: Optional[str]) -> List[SimpleNamespace]:
    """Return forecast rows joined with account data."""
    q = (
        db.query(
            Forecast.period,
            Forecast.account_id,
            Forecast.amount.label("forecast_amount"),
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            Account.type.label("account_type"),
        )
        .join(Account, Forecast.account_id == Account.id)
    )
    if period:
        q = q.filter(Forecast.period == period)
    return [SimpleNamespace(**dict(row._mapping)) for row in q.all()]


@router.get(
    "/variance",
    response_model=List[VarianceReport],
    summary="Budget vs actual variance report",
    description=(
        "Returns budget vs actual variance per account per period. "
        "Optionally filter to a single period (e.g. '2024-Q1')."
    ),
)
def variance_report(
    period: Optional[str] = Query(default=None, description="Period to filter, e.g. '2024-Q1'"),
    db: Session = Depends(get_db),
) -> List[VarianceReport]:
    budgets = _budget_rows(db, period)
    actuals = _actual_rows(db, period)
    return compute_variance(budgets, actuals)


@router.get(
    "/forecast-accuracy",
    response_model=List[ForecastAccuracyReport],
    summary="Forecast accuracy report",
    description=(
        "Compares forecast amounts against actuals to measure prediction accuracy. "
        "Optionally filter to a single period."
    ),
)
def forecast_accuracy_report(
    period: Optional[str] = Query(default=None, description="Period to filter, e.g. '2024-Q1'"),
    db: Session = Depends(get_db),
) -> List[ForecastAccuracyReport]:
    forecasts = _forecast_rows(db, period)
    actuals = _actual_rows(db, period)
    return compute_forecast_accuracy(forecasts, actuals)


@router.get(
    "/cash-flow",
    response_model=List[CashFlowSummary],
    summary="Cash flow summary",
    description=(
        "Aggregates revenue and expense actuals into a period-by-period cash flow "
        "timeline with cumulative net income."
    ),
)
def cash_flow_report(db: Session = Depends(get_db)) -> List[CashFlowSummary]:
    actuals = _actual_rows(db, period=None)
    return compute_cash_flow(actuals)


@router.get(
    "/period-summary",
    response_model=List[PeriodSummary],
    summary="Period summary report",
    description=(
        "High-level roll-up of budgeted vs actual revenue and expense per period, "
        "including net budget, net actual, and net variance."
    ),
)
def period_summary_report(db: Session = Depends(get_db)) -> List[PeriodSummary]:
    budgets = _budget_rows(db, period=None)
    actuals = _actual_rows(db, period=None)
    return compute_period_summary(budgets, actuals)
