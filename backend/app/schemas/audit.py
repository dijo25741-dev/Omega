from datetime import datetime
from typing import List
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    event: str
    module: str
    user: str
    decision: str
    reason: str
    confidence_score: float
    status: str

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    total: int
    logs: List[AuditLogResponse]
    page: int
    limit: int
