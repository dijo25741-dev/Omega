from datetime import datetime, UTC
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PlantState(Base):
    __tablename__ = "plant_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    water_level: Mapped[float] = mapped_column(Float, nullable=False)
    pressure: Mapped[float] = mapped_column(Float, nullable=False)
    flow_rate: Mapped[float] = mapped_column(Float, nullable=False)
    pump_status: Mapped[str] = mapped_column(String(10), nullable=False) # "ON" or "OFF"
    inlet_valve_status: Mapped[str] = mapped_column(String(10), nullable=False) # "OPEN" or "CLOSED"
    outlet_valve_status: Mapped[str] = mapped_column(String(10), nullable=False) # "OPEN" or "CLOSED"
