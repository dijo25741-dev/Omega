from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.simulator import simulator_service
from app.schemas.plant import PlantTelemetryResponse, PlantResetResponse
from app.audit.logger import log_event

router = APIRouter(prefix="/plant", tags=["Plant"])

@router.get("/status", response_model=PlantTelemetryResponse)
async def get_plant_status():
    """Gets the current real-time telemetry from the water treatment plant."""
    return simulator_service.plant.get_telemetry()

@router.post("/reset", response_model=PlantResetResponse)
async def reset_plant():
    """Resets the water plant physical parameters and clears PLC blockages."""
    simulator_service.plant.reset()
    simulator_service.plc.emergency_stopped = False
    simulator_service.plc.safety_trip = False
    simulator_service.plc.safety_override_active = False
    simulator_service.plc.pump_status = "OFF"
    simulator_service.plc.inlet_valve_status = "OPEN"
    simulator_service.plc.outlet_valve_status = "CLOSED"
    simulator_service.risk.reset()
    
    await log_event(
        event="Plant Reset Executed",
        module="PLANT",
        user="OPERATOR",
        decision="RESET",
        reason="Manual operator intervention to normalize system",
        confidence_score=1.0,
        status="SUCCESS"
    )
    
    return {"success": True, "message": "Water treatment plant and PLC state reset completed"}
