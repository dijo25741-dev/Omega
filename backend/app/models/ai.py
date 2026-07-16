from datetime import datetime, UTC
from sqlalchemy import String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AIAlert(Base):
    __tablename__ = "ai_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)       # e.g., 'ALLOWED', 'BLOCKED', 'HIGH_RISK_ALERT'
    threat_stage: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g., 'Normal', 'PLC Targeting'
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)     # e.g., 'Low', 'Medium', 'High', 'Critical'
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_text: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Store dynamic JSON values
    shap_attributions: Mapped[dict] = mapped_column(JSON, nullable=True)
    shap_chart_base64: Mapped[str] = mapped_column(String, nullable=True)
    incident_playbook: Mapped[dict] = mapped_column(JSON, nullable=True)
