from fastapi import APIRouter
from app.services.simulator import simulator_service
from app.schemas.communication import RouteRotateResponse
from app.audit.logger import log_event

router = APIRouter(prefix="/communication", tags=["Communication Orchestrator"])

@router.get("")
async def get_communication_status():
    """Gets the current active secure route and exposed SCADA services list."""
    return simulator_service.comms.get_state()

@router.post("/rotate", response_model=RouteRotateResponse)
async def rotate_communication_route():
    """Manually forces a secure route rotation and session reset."""
    rot_details = simulator_service.comms.rotate_route()
    
    await log_event(
        event="Manual Communication Rotation",
        module="COMMUNICATION",
        user="OPERATOR",
        decision="ROTATE",
        reason="Manual operator request to rotate routing channel",
        confidence_score=1.0,
        status="SUCCESS"
    )
    
    return {
        "success": True,
        "active_route": rot_details["active_route"],
        "session_id": rot_details["session_id"],
        "message": rot_details["event"]
    }
