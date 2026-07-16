from datetime import datetime
from typing import List, Union
from pydantic import BaseModel, field_validator

class CommunicationStateResponse(BaseModel):
    id: int
    timestamp: datetime
    active_route: str
    session_id: str
    exposed_services: Union[str, List[str]]
    session_rotated: bool

    @field_validator("exposed_services", mode="before")
    @classmethod
    def split_services(cls, v):
        if isinstance(v, str):
            if not v:
                return []
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    class Config:
        from_attributes = True

class RouteRotateResponse(BaseModel):
    success: bool
    active_route: str
    session_id: str
    message: str
