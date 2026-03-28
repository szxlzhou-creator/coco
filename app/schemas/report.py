from typing import Optional

from pydantic import BaseModel


class VarianceReport(BaseModel):
    """Budget vs actual variance for a given period and account."""

    period: str
    account_code: str
    account_name: str
    account_type: str
    budget_amount: float
    actual_amount: float
    variance_amount: float
    variance_pct: Optional[float]


class ForecastAccuracyReport(BaseModel):
    """Forecast accuracy measured against actuals."""

    period: str
    account_code: str
    account_name: str
    forecast_amount: float
    actual_amount: float
    accuracy_pct: Optional[float]


class CashFlowSummary(BaseModel):
    """Aggregated cash flow by period."""

    period: str
    total_revenue: float
    total_expense: float
    net_income: float
    cumulative_net_income: float


class PeriodSummary(BaseModel):
    """High-level budget vs actual summary per period."""

    period: str
    budgeted_revenue: float
    actual_revenue: float
    budgeted_expense: float
    actual_expense: float
    net_budget: float
    net_actual: float
    net_variance: float
