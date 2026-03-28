"""
Integration tests for the Coco FP&A API.

All tests use an in-memory SQLite database via dependency override so they
are isolated, fast, and do not touch the production coco.db file.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_db

# Ensure all ORM models are registered with Base.metadata before create_all
import app.models.account  # noqa: F401
import app.models.actual  # noqa: F401
import app.models.budget  # noqa: F401
import app.models.forecast  # noqa: F401

from app.main import app  # noqa: E402 — imported after model registration

# ---------------------------------------------------------------------------
# In-memory test database setup
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _create_account(code="1000", name="Revenue", acc_type="revenue"):
    return client.post(
        "/accounts/",
        json={"code": code, "name": name, "type": acc_type},
    )


def _create_budget(account_id: int, period="2024-Q1", amount=10000.0):
    return client.post(
        "/budgets/",
        json={"account_id": account_id, "period": period, "amount": amount},
    )


def _create_actual(account_id: int, period="2024-Q1", amount=9500.0, date="2024-01-31"):
    return client.post(
        "/actuals/",
        json={
            "account_id": account_id,
            "period": period,
            "amount": amount,
            "transaction_date": date,
        },
    )


def _create_forecast(account_id: int, period="2024-Q2", amount=11000.0):
    return client.post(
        "/forecasts/",
        json={
            "account_id": account_id,
            "period": period,
            "amount": amount,
            "confidence": 0.9,
            "method": "manual",
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Coco FP&A API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


# ---------------------------------------------------------------------------
# Account CRUD
# ---------------------------------------------------------------------------

def test_create_account():
    resp = _create_account()
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "1000"
    assert data["name"] == "Revenue"
    assert data["type"] == "revenue"
    assert "id" in data


def test_create_account_duplicate_code():
    _create_account()
    resp = _create_account()
    assert resp.status_code == 409


def test_list_accounts():
    _create_account("1000", "Revenue", "revenue")
    _create_account("2000", "COGS", "expense")
    resp = client.get("/accounts/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_account():
    created = _create_account().json()
    resp = client.get(f"/accounts/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["code"] == "1000"


def test_get_account_not_found():
    resp = client.get("/accounts/9999")
    assert resp.status_code == 404


def test_update_account():
    created = _create_account().json()
    resp = client.put(f"/accounts/{created['id']}", json={"name": "Total Revenue"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Total Revenue"


def test_delete_account():
    created = _create_account().json()
    resp = client.delete(f"/accounts/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/accounts/{created['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Budget CRUD
# ---------------------------------------------------------------------------

def test_create_budget():
    acct = _create_account().json()
    resp = _create_budget(acct["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 10000.0
    assert data["period"] == "2024-Q1"


def test_list_budgets_filter():
    acct = _create_account().json()
    _create_budget(acct["id"], "2024-Q1", 10000)
    _create_budget(acct["id"], "2024-Q2", 12000)
    resp = client.get("/budgets/?period=2024-Q1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["period"] == "2024-Q1"


def test_update_budget():
    acct = _create_account().json()
    bgt = _create_budget(acct["id"]).json()
    resp = client.put(f"/budgets/{bgt['id']}", json={"amount": 15000.0})
    assert resp.status_code == 200
    assert resp.json()["amount"] == 15000.0


def test_delete_budget():
    acct = _create_account().json()
    bgt = _create_budget(acct["id"]).json()
    resp = client.delete(f"/budgets/{bgt['id']}")
    assert resp.status_code == 204
    assert client.get(f"/budgets/{bgt['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Actual CRUD
# ---------------------------------------------------------------------------

def test_create_actual():
    acct = _create_account().json()
    resp = _create_actual(acct["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 9500.0
    assert data["transaction_date"] == "2024-01-31"


def test_list_actuals_filter():
    acct = _create_account().json()
    _create_actual(acct["id"], "2024-Q1", 9500, "2024-01-31")
    _create_actual(acct["id"], "2024-Q2", 9800, "2024-04-30")
    resp = client.get("/actuals/?period=2024-Q2")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_actual():
    acct = _create_account().json()
    act = _create_actual(acct["id"]).json()
    resp = client.put(f"/actuals/{act['id']}", json={"amount": 9750.0})
    assert resp.status_code == 200
    assert resp.json()["amount"] == 9750.0


def test_delete_actual():
    acct = _create_account().json()
    act = _create_actual(acct["id"]).json()
    resp = client.delete(f"/actuals/{act['id']}")
    assert resp.status_code == 204
    assert client.get(f"/actuals/{act['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Forecast CRUD
# ---------------------------------------------------------------------------

def test_create_forecast():
    acct = _create_account().json()
    resp = _create_forecast(acct["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 11000.0
    assert data["confidence"] == 0.9
    assert data["method"] == "manual"


def test_list_forecasts_filter():
    acct = _create_account().json()
    _create_forecast(acct["id"], "2024-Q2", 11000)
    _create_forecast(acct["id"], "2024-Q3", 12000)
    resp = client.get("/forecasts/?period=2024-Q3")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_forecast():
    acct = _create_account().json()
    fc = _create_forecast(acct["id"]).json()
    resp = client.put(f"/forecasts/{fc['id']}", json={"confidence": 0.75})
    assert resp.status_code == 200
    assert resp.json()["confidence"] == 0.75


def test_delete_forecast():
    acct = _create_account().json()
    fc = _create_forecast(acct["id"]).json()
    resp = client.delete(f"/forecasts/{fc['id']}")
    assert resp.status_code == 204
    assert client.get(f"/forecasts/{fc['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def test_variance_report():
    acct = _create_account().json()
    _create_budget(acct["id"], "2024-Q1", 10000)
    _create_actual(acct["id"], "2024-Q1", 9500, "2024-01-31")

    resp = client.get("/reports/variance?period=2024-Q1")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["budget_amount"] == 10000.0
    assert row["actual_amount"] == 9500.0
    assert row["variance_amount"] == -500.0
    assert row["variance_pct"] == -5.0


def test_variance_report_no_actuals():
    acct = _create_account().json()
    _create_budget(acct["id"], "2024-Q1", 10000)

    resp = client.get("/reports/variance?period=2024-Q1")
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["actual_amount"] == 0.0
    assert row["variance_amount"] == -10000.0


def test_cash_flow_report():
    rev_acct = _create_account("1000", "Revenue", "revenue").json()
    exp_acct = _create_account("2000", "Expenses", "expense").json()

    _create_actual(rev_acct["id"], "2024-Q1", 50000, "2024-01-31")
    _create_actual(exp_acct["id"], "2024-Q1", 30000, "2024-01-31")
    _create_actual(rev_acct["id"], "2024-Q2", 55000, "2024-04-30")
    _create_actual(exp_acct["id"], "2024-Q2", 32000, "2024-04-30")

    resp = client.get("/reports/cash-flow")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2

    q1 = rows[0]
    assert q1["period"] == "2024-Q1"
    assert q1["total_revenue"] == 50000.0
    assert q1["total_expense"] == 30000.0
    assert q1["net_income"] == 20000.0
    assert q1["cumulative_net_income"] == 20000.0

    q2 = rows[1]
    assert q2["net_income"] == 23000.0
    assert q2["cumulative_net_income"] == 43000.0


def test_forecast_accuracy_report():
    acct = _create_account().json()
    _create_forecast(acct["id"], "2024-Q1", 10000)
    _create_actual(acct["id"], "2024-Q1", 9000, "2024-01-31")

    resp = client.get("/reports/forecast-accuracy?period=2024-Q1")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    # accuracy = 100 - abs((10000 - 9000) / 9000 * 100) = 100 - 11.111... ≈ 88.8889
    assert rows[0]["accuracy_pct"] is not None
    assert abs(rows[0]["accuracy_pct"] - 88.8889) < 0.01


def test_period_summary_report():
    rev_acct = _create_account("1000", "Revenue", "revenue").json()
    exp_acct = _create_account("2000", "Expenses", "expense").json()

    _create_budget(rev_acct["id"], "2024-Q1", 10000)
    _create_budget(exp_acct["id"], "2024-Q1", 6000)
    _create_actual(rev_acct["id"], "2024-Q1", 9500, "2024-01-31")
    _create_actual(exp_acct["id"], "2024-Q1", 5800, "2024-01-31")

    resp = client.get("/reports/period-summary")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["budgeted_revenue"] == 10000.0
    assert row["actual_revenue"] == 9500.0
    assert row["budgeted_expense"] == 6000.0
    assert row["actual_expense"] == 5800.0
    assert row["net_budget"] == 4000.0
    assert row["net_actual"] == 3700.0
    assert row["net_variance"] == -300.0
