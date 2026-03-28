# Coco — AI-native FP&A API

**Coco** is an AI-native Financial Planning & Analysis (FP&A) REST API built for personal-copilot agents. It exposes structured, agent-friendly endpoints for budgets, actuals, forecasts, and variance analysis so that AI agents can query, plan, and reason about financial data without any ambiguity.

## Features

| Feature | Description |
|---|---|
| **Chart of Accounts** | Master list of revenue, expense, asset, liability, and equity accounts |
| **Budgets** | Planned amounts per account per period |
| **Actuals** | Recorded financial transactions mapped to accounts and periods |
| **Forecasts** | Forward-looking projections with confidence scores and forecasting method |
| **Variance Analysis** | Budget vs. actual comparison with variance amount and % |
| **Forecast Accuracy** | Forecast vs. actual comparison |
| **Cash Flow Timeline** | Net income and cumulative cash position over time |
| **Period Summary** | Revenue, expense, and net income summary per period |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload

# Open interactive API docs (agent-readable OpenAPI spec)
open http://localhost:8000/docs
```

## API Overview

```
GET  /                          # Health check — returns service metadata
GET  /accounts                  # List all accounts
POST /accounts                  # Create an account
GET  /accounts/{id}             # Get account by ID
PUT  /accounts/{id}             # Update account
DELETE /accounts/{id}           # Delete account

GET  /budgets?period=&account_id=   # List budgets (filterable)
POST /budgets                       # Create budget line
GET  /budgets/{id}
PUT  /budgets/{id}
DELETE /budgets/{id}

GET  /actuals?period=&account_id=   # List actuals (filterable)
POST /actuals
GET  /actuals/{id}
PUT  /actuals/{id}
DELETE /actuals/{id}

GET  /forecasts?period=&account_id= # List forecasts (filterable)
POST /forecasts
GET  /forecasts/{id}
PUT  /forecasts/{id}
DELETE /forecasts/{id}

GET  /reports/variance?period=          # Budget vs. actual variance
GET  /reports/forecast-accuracy?period= # Forecast vs. actual accuracy
GET  /reports/cash-flow                 # Cash flow timeline
GET  /reports/period-summary            # Revenue/expense summary per period
```

## Agent Usage

The API is designed to be consumed directly by AI copilot agents:

- **OpenAPI spec** at `/openapi.json` — agents can introspect all endpoints and schemas
- **Filterable list endpoints** — `?period=2024-Q1` narrows results without ambiguity
- **Structured report payloads** — every report field is named and typed (no raw arrays)
- **Health check** at `GET /` — lets agents confirm reachability before planning

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
app/
├── main.py          # FastAPI application entry point
├── database.py      # SQLAlchemy SQLite setup
├── models/          # ORM models (Account, Budget, Actual, Forecast)
├── schemas/         # Pydantic v2 request/response schemas + report schemas
├── routers/         # API route handlers
└── services/
    └── analytics.py # Pure analytics functions (variance, cash flow, etc.)
tests/
└── test_api.py      # 25 pytest tests with in-memory SQLite
```
