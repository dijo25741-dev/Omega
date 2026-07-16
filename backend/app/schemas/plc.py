from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class PLCStateResponse(BaseModel):
    id: int
    timestamp: datetime
    pump_status: str
    inlet_valve_status: str
    outlet_valve_status: str
    emergency_stopped: bool
    safety_trip: bool
    last_command: Optional[str] = None
    last_command_status: Optional[str] = None

    class Config:
        from_attributes = True

class PLCCommandRequest(BaseModel):
    command: str  # "START_PUMP", "STOP_PUMP", "OPEN_INLET", "CLOSE_INLET", etc.
    override_safety: bool = False

class PLCCommandResponse(BaseModel):
    success: bool
    detail: str
    state: dict
class PLCSimpleCommandResponse(BaseModel):
    success: bool
    detail: str
