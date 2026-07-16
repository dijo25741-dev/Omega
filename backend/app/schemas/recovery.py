from datetime import datetime
from pydantic import BaseModel

class RecoveryStateResponse(BaseModel):
    id: int
    timestamp: datetime
    in_progress: bool
    stage: str
    percentage: float
    est_seconds_remaining: float
    system_health: float

    class Config:
        from_attributes = True

class RecoveryStartResponse(BaseModel):
    success: bool
    message: str
