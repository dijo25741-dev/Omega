from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PLCState(Base):
    __tablename__ = "plc_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    pump_status: Mapped[str] = mapped_column(String(10), nullable=False) # "ON" or "OFF"
    inlet_valve_status: Mapped[str] = mapped_column(String(10), nullable=False) # "OPEN" or "CLOSED"
    outlet_valve_status: Mapped[str] = mapped_column(String(10), nullable=False) # "OPEN" or "CLOSED"
    emergency_stopped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_trip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_command: Mapped[str] = mapped_column(String(50), nullable=True)
    last_command_status: Mapped[str] = mapped_column(String(20), nullable=True) # "SUCCESS" or "REJECTED"
