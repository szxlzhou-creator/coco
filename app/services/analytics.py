"""
Analytics service: pure functions that compute FP&A reports from ORM objects.
All functions return plain Pydantic schema instances — no DB access here.
"""

from collections import defaultdict
from typing import Any, List

from app.schemas.report import (
    CashFlowSummary,
    ForecastAccuracyReport,
    PeriodSummary,
    VarianceReport,
)


def compute_variance(budgets: List[Any], actuals: List[Any]) -> List[VarianceReport]:
    """
    Compare budget vs actual amounts grouped by (period, account).

    Args:
        budgets: list of Budget ORM objects (with .account relationship loaded
                 OR account_id / account attributes available via join).
        actuals: list of Actual ORM objects.

    Returns:
        Sorted list of VarianceReport instances.
    """
    # Index actuals by (period, account_id)
    actual_map: dict = defaultdict(float)
    for actual in actuals:
        actual_map[(actual.period, actual.account_id)] += actual.amount

    results: List[VarianceReport] = []
    for budget in budgets:
        key = (budget.period, budget.account_id)
        actual_amount = actual_map.get(key, 0.0)
        variance_amount = actual_amount - budget.budget_amount
        variance_pct = (
            round(variance_amount / budget.budget_amount * 100, 4)
            if budget.budget_amount != 0
            else None
        )
        results.append(
            VarianceReport(
                period=budget.period,
                account_code=budget.account_code,
                account_name=budget.account_name,
                account_type=budget.account_type,
                budget_amount=budget.budget_amount,
                actual_amount=actual_amount,
                variance_amount=round(variance_amount, 4),
                variance_pct=variance_pct,
            )
        )
    results.sort(key=lambda r: (r.period, r.account_code))
    return results


def compute_forecast_accuracy(
    forecasts: List[Any], actuals: List[Any]
) -> List[ForecastAccuracyReport]:
    """
    Measure forecast accuracy against actuals grouped by (period, account).

    accuracy_pct = 100 - abs((forecast - actual) / actual * 100)
    Returns None when actual_amount is 0.
    """
    actual_map: dict = defaultdict(float)
    for actual in actuals:
        actual_map[(actual.period, actual.account_id)] += actual.amount

    results: List[ForecastAccuracyReport] = []
    for forecast in forecasts:
        key = (forecast.period, forecast.account_id)
        actual_amount = actual_map.get(key, 0.0)
        if actual_amount != 0:
            accuracy_pct = round(
                100.0 - abs((forecast.forecast_amount - actual_amount) / actual_amount * 100),
                4,
            )
        else:
            accuracy_pct = None
        results.append(
            ForecastAccuracyReport(
                period=forecast.period,
                account_code=forecast.account_code,
                account_name=forecast.account_name,
                forecast_amount=forecast.forecast_amount,
                actual_amount=actual_amount,
                accuracy_pct=accuracy_pct,
            )
        )
    results.sort(key=lambda r: (r.period, r.account_code))
    return results


def compute_cash_flow(actuals_by_period: List[Any]) -> List[CashFlowSummary]:
    """
    Summarise revenue and expense actuals into a cash-flow timeline.

    Args:
        actuals_by_period: list of objects with attributes
            period, account_type, amount.

    Returns:
        Chronologically sorted list of CashFlowSummary instances.
    """
    # Aggregate per period
    period_revenue: dict = defaultdict(float)
    period_expense: dict = defaultdict(float)

    for actual in actuals_by_period:
        if actual.account_type == "revenue":
            period_revenue[actual.period] += actual.amount
        elif actual.account_type == "expense":
            period_expense[actual.period] += actual.amount

    all_periods = sorted(set(list(period_revenue.keys()) + list(period_expense.keys())))

    results: List[CashFlowSummary] = []
    cumulative = 0.0
    for period in all_periods:
        revenue = round(period_revenue[period], 4)
        expense = round(period_expense[period], 4)
        net = round(revenue - expense, 4)
        cumulative = round(cumulative + net, 4)
        results.append(
            CashFlowSummary(
                period=period,
                total_revenue=revenue,
                total_expense=expense,
                net_income=net,
                cumulative_net_income=cumulative,
            )
        )
    return results


def compute_period_summary(
    budgets: List[Any], actuals: List[Any]
) -> List[PeriodSummary]:
    """
    Produce a per-period roll-up of budgeted vs actual revenue and expense.

    Args:
        budgets: list of objects with period, account_type, budget_amount.
        actuals: list of objects with period, account_type, amount.

    Returns:
        Chronologically sorted list of PeriodSummary instances.
    """
    budget_revenue: dict = defaultdict(float)
    budget_expense: dict = defaultdict(float)
    actual_revenue: dict = defaultdict(float)
    actual_expense: dict = defaultdict(float)

    for budget in budgets:
        if budget.account_type == "revenue":
            budget_revenue[budget.period] += budget.budget_amount
        elif budget.account_type == "expense":
            budget_expense[budget.period] += budget.budget_amount

    for actual in actuals:
        if actual.account_type == "revenue":
            actual_revenue[actual.period] += actual.amount
        elif actual.account_type == "expense":
            actual_expense[actual.period] += actual.amount

    all_periods = sorted(
        set(
            list(budget_revenue.keys())
            + list(budget_expense.keys())
            + list(actual_revenue.keys())
            + list(actual_expense.keys())
        )
    )

    results: List[PeriodSummary] = []
    for period in all_periods:
        b_rev = round(budget_revenue[period], 4)
        a_rev = round(actual_revenue[period], 4)
        b_exp = round(budget_expense[period], 4)
        a_exp = round(actual_expense[period], 4)
        net_budget = round(b_rev - b_exp, 4)
        net_actual = round(a_rev - a_exp, 4)
        results.append(
            PeriodSummary(
                period=period,
                budgeted_revenue=b_rev,
                actual_revenue=a_rev,
                budgeted_expense=b_exp,
                actual_expense=a_exp,
                net_budget=net_budget,
                net_actual=net_actual,
                net_variance=round(net_actual - net_budget, 4),
            )
        )
    return results
