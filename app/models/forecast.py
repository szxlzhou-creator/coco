from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    period = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    method = Column(String, nullable=False, default="manual")  # manual, linear_trend, moving_average
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
