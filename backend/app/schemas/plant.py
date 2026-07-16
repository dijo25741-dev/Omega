from datetime import datetime
from pydantic import BaseModel

class PlantTelemetryResponse(BaseModel):
    water_level: float
    pressure: float
    flow_rate: float
    pump_status: str
    inlet_valve_status: str
    outlet_valve_status: str

class PlantStateResponse(PlantTelemetryResponse):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PlantResetResponse(BaseModel):
    success: bool
    message: str
