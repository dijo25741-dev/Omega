from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CommunicationState(Base):
    __tablename__ = "communication_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    active_route: Mapped[str] = mapped_column(String(50), nullable=False) # "Secure Route A", "Secure Route B", etc.
    session_id: Mapped[str] = mapped_column(String(100), nullable=False) # Session UUID
    exposed_services: Mapped[str] = mapped_column(String(255), nullable=False) # Comma-separated list
    session_rotated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
