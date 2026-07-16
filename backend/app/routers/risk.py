from fastapi import APIRouter
from app.services.simulator import simulator_service
from app.schemas.risk import RiskSimulateRequest, RiskSimulateResponse
from app.audit.logger import log_event

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

@router.get("")
async def get_risk_status():
    """Gets the current threat risk score and level."""
    return simulator_service.risk.get_state()

@router.post("/simulate", response_model=RiskSimulateResponse)
async def simulate_risk_event(payload: RiskSimulateRequest):
    """Simulates a threat event, directly injecting risk points into the scoring engine."""
    new_score = simulator_service.risk.add_risk_event(payload.event_name, payload.points)
    state = simulator_service.risk.get_state()
    
    await log_event(
        event=f"Simulated Risk Injected: {payload.event_name}",
        module="RISK",
        user="OPERATOR",
        decision="INJECT",
        reason=f"Manual threat score simulation of +{payload.points} pts",
        confidence_score=1.0,
        status="WARNING"
    )
    
    return {
        "success": True,
        "risk_score": new_score,
        "risk_level": state["risk_level"],
        "message": f"Successfully injected risk event. Level is now {state['risk_level']}."
    }
