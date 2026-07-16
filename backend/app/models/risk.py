from datetime import datetime, UTC
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class RiskState(Base):
    __tablename__ = "risk_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False) # 0.0 to 100.0
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False) # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    reason: Mapped[str] = mapped_column(String(255), nullable=True) # Description of triggers
