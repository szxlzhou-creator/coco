from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import accounts, actuals, budgets, forecasts, reports

tags_metadata = [
    {
        "name": "Accounts",
        "description": "Chart of accounts — the master list of revenue, expense, asset, liability, and equity accounts.",
    },
    {
        "name": "Budgets",
        "description": "Budget line items — planned amounts per account per period.",
    },
    {
        "name": "Actuals",
        "description": "Actual financial entries — recorded transactions mapped to accounts and periods.",
    },
    {
        "name": "Forecasts",
        "description": "Forward-looking forecasts — projected amounts with confidence scores and forecasting method.",
    },
    {
        "name": "Reports",
        "description": (
            "Read-only analytics endpoints: variance analysis, forecast accuracy, "
            "cash flow timeline, and period summaries."
        ),
    },
]


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Coco FP&A API",
    description=(
        "AI-native Financial Planning & Analysis API for personal-copilot agents. "
        "Provides structured access to budgets, actuals, forecasts, and variance analysis."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


app.include_router(accounts.router)
app.include_router(budgets.router)
app.include_router(actuals.router)
app.include_router(forecasts.router)
app.include_router(reports.router)


@app.get(
    "/",
    summary="Service health check",
    description="Returns basic service metadata. Useful for agents to confirm the API is reachable.",
    tags=["Health"],
)
def root() -> dict:
    return {"service": "Coco FP&A API", "version": "1.0.0", "docs": "/docs"}
