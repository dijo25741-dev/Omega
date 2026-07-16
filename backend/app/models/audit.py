from datetime import datetime, UTC
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    event: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "PLC Command Sent", "Route Rotated"
    module: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "PLC", "COMMUNICATION", "SECURITY", "RISK"
    user: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "OPERATOR", "SYSTEM", "RISK_ENGINE"
    decision: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "ALLOW", "BLOCK", "ADAPT"
    reason: Mapped[str] = mapped_column(String(255), nullable=False) # Explanation
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False) # 0.0 to 1.0 (relevance/certainty)
    status: Mapped[str] = mapped_column(String(20), nullable=False) # "SUCCESS", "FAILURE", "WARNING"
