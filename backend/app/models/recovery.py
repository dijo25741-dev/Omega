from datetime import datetime, UTC
from sqlalchemy import String, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class RecoveryState(Base):
    __tablename__ = "recovery_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    in_progress: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False) # "NONE", "CONTAIN", "RECOVER", "VERIFY", "RESUME"
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # 0.0 to 100.0
    est_seconds_remaining: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    system_health: Mapped[float] = mapped_column(Float, default=100.0, nullable=False) # 0.0 to 100.0
