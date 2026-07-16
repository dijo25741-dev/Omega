import time
from fastapi import APIRouter
from app.services.simulator import simulator_service

router = APIRouter(prefix="/health", tags=["Health"])

startup_time = time.time()

@router.get("")
async def get_health():
    """Gets the status of the server, uptime, and database connectivity."""
    uptime = time.time() - startup_time
    return {
        "status": "HEALTHY",
        "uptime_seconds": round(uptime, 2),
        "simulator_active": simulator_service._running,
        "app_name": "Omega Cyber Resilience Core Backend"
    }
