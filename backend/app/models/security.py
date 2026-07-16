from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SecurityState(Base):
    __tablename__ = "security_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False) # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    monitoring_frequency: Mapped[str] = mapped_column(String(20), nullable=False) # "NORMAL", "HIGH", "CRITICAL"
    attack_surface_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
