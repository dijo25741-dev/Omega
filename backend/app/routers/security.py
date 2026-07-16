from fastapi import APIRouter, HTTPException, status
from app.services.simulator import simulator_service
from app.schemas.security import SecurityUpdateRequest, SecurityUpdateResponse
from app.audit.logger import log_event

router = APIRouter(prefix="/security", tags=["Security Engine"])

@router.get("")
async def get_security_status():
    """Gets the current active system security posture configuration."""
    return simulator_service.security.get_state()

@router.post("/update", response_model=SecurityUpdateResponse)
async def update_security_level(payload: SecurityUpdateRequest):
    """Manually overwrites the active security posture level."""
    lvl = payload.level.upper()
    if lvl not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid security level. Must be LOW, MEDIUM, HIGH, or CRITICAL."
        )

    # Force security engine adjustment
    sec_update = simulator_service.security.adapt_to_risk(lvl)
    # Also adjust communication services accordingly
    simulator_service.comms.adapt_to_risk(lvl)

    # Calculate audit reason
    changes_desc = ", ".join(sec_update["changes"]) if sec_update["changes"] else "No security policy details changed"
    await log_event(
        event=f"Security Level Manually Overridden to {lvl}",
        module="SECURITY",
        user="OPERATOR",
        decision="UPDATE",
        reason=f"Operator manually updated security posture. Status modifications: {changes_desc}",
        confidence_score=1.0,
        status="SUCCESS"
    )

    return {
        "success": True,
        "level": lvl,
        "details": f"Security settings updated: {changes_desc}"
    }
