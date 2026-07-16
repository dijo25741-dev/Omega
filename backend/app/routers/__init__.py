from app.routers.plant import router as plant_router
from app.routers.plc import router as plc_router
from app.routers.communication import router as communication_router
from app.routers.security import router as security_router
from app.routers.risk import router as risk_router
from app.routers.recovery import router as recovery_router
from app.routers.audit import router as audit_router
from app.routers.health import router as health_router
from app.routers.attack import router as attack_router

__all__ = [
    "plant_router",
    "plc_router",
    "communication_router",
    "security_router",
    "risk_router",
    "recovery_router",
    "audit_router",
    "health_router",
    "attack_router"
]
