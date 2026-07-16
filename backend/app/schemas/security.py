from datetime import datetime
from pydantic import BaseModel

class SecurityStateResponse(BaseModel):
    id: int
    timestamp: datetime
    level: str
    monitoring_frequency: str
    attack_surface_restricted: bool
    auth_required: bool
    mfa_enabled: bool

    class Config:
        from_attributes = True

class SecurityUpdateRequest(BaseModel):
    level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"

class SecurityUpdateResponse(BaseModel):
    success: bool
    level: str
    details: str
