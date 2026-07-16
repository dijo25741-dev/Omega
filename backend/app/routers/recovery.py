from fastapi import APIRouter, HTTPException, status
from app.services.simulator import simulator_service
from app.schemas.recovery import RecoveryStartResponse
from app.audit.logger import log_event

router = APIRouter(prefix="/recovery", tags=["Recovery Engine"])

@router.get("")
async def get_recovery_status():
    """Gets the active self-healing process state and estimated completion time."""
    return simulator_service.recovery.get_state()

@router.post("/start", response_model=RecoveryStartResponse)
async def start_recovery():
    """Manually initiates the containment and recovery process."""
    success, message = simulator_service.recovery.start_recovery()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
        
    await log_event(
        event="Manual Recovery Action Initiated",
        module="RECOVERY",
        user="OPERATOR",
        decision="RESTORE",
        reason="Operator manually engaged automated self-healing sequence",
        confidence_score=1.0,
        status="SUCCESS"
    )
    
    return {"success": True, "message": message}
