from datetime import datetime
from pydantic import BaseModel

class RiskStateResponse(BaseModel):
    id: int
    timestamp: datetime
    risk_score: float
    risk_level: str
    reason: str

    class Config:
        from_attributes = True

class RiskSimulateRequest(BaseModel):
    event_name: str
    points: float

class RiskSimulateResponse(BaseModel):
    success: bool
    risk_score: float
    risk_level: str
    message: str
