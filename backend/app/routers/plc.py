from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.simulator import simulator_service
from app.schemas.plc import PLCStateResponse, PLCCommandResponse, PLCSimpleCommandResponse
from app.audit.logger import log_event

router = APIRouter(prefix="/plc", tags=["PLC"])

class ValveControl(BaseModel):
    valve: str = Field(..., pattern="^(inlet|outlet)$", description="The valve to operate ('inlet' or 'outlet')")
    mfa_token: Optional[str] = Field(None, description="Simulated MFA token (required when security is HIGH or CRITICAL)")

class PumpControl(BaseModel):
    mfa_token: Optional[str] = Field(None, description="Simulated MFA token (required when security is HIGH or CRITICAL)")

def verify_adaptive_security(mfa_token: Optional[str]):
    """Enforces adaptive multi-factor authentication if enabled by Security Engine."""
    security_state = simulator_service.security.get_state()
    if security_state["mfa_enabled"]:
        if not mfa_token or mfa_token != "123456":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA token required or invalid. Adaptive security policy is active. Use token '123456'."
            )

@router.get("/status")
async def get_plc_status():
    """Gets the current virtual PLC register state."""
    state = simulator_service.plc.get_state()
    return {
        "pump_status": simulator_service.plc.pump_status,
        "inlet_valve_status": simulator_service.plc.inlet_valve_status,
        "outlet_valve_status": simulator_service.plc.outlet_valve_status,
        **state
    }

@router.post("/start-pump", response_model=PLCCommandResponse)
async def start_pump(payload: Optional[PumpControl] = None):
    """Starts the water inlet pump."""
    token = payload.mfa_token if payload else None
    verify_adaptive_security(token)
    
    plant_state = simulator_service.plant.get_telemetry()
    success, detail = simulator_service.plc.process_command("START_PUMP", plant_state)
    
    await log_event(
        event="PLC Start Pump command sent",
        module="PLC",
        user="OPERATOR",
        decision="ALLOW" if success else "BLOCK",
        reason=detail,
        status="SUCCESS" if success else "FAILURE"
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
    return {
        "success": True,
        "detail": detail,
        "state": get_plc_status_snapshot()
    }

@router.post("/stop-pump", response_model=PLCCommandResponse)
async def stop_pump(payload: Optional[PumpControl] = None):
    """Stops the water inlet pump."""
    # Stopping a pump doesn't require MFA for safety/emergency access
    plant_state = simulator_service.plant.get_telemetry()
    success, detail = simulator_service.plc.process_command("STOP_PUMP", plant_state)
    
    await log_event(
        event="PLC Stop Pump command sent",
        module="PLC",
        user="OPERATOR",
        decision="ALLOW" if success else "BLOCK",
        reason=detail,
        status="SUCCESS" if success else "FAILURE"
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
    return {
        "success": True,
        "detail": detail,
        "state": get_plc_status_snapshot()
    }

@router.post("/open-valve", response_model=PLCCommandResponse)
async def open_valve(payload: ValveControl):
    """Opens either the inlet or outlet valve."""
    verify_adaptive_security(payload.mfa_token)
    
    cmd = "OPEN_INLET" if payload.valve == "inlet" else "OPEN_OUTLET"
    plant_state = simulator_service.plant.get_telemetry()
    success, detail = simulator_service.plc.process_command(cmd, plant_state)
    
    await log_event(
        event=f"PLC Open Valve ({payload.valve}) command sent",
        module="PLC",
        user="OPERATOR",
        decision="ALLOW" if success else "BLOCK",
        reason=detail,
        status="SUCCESS" if success else "FAILURE"
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
    return {
        "success": True,
        "detail": detail,
        "state": get_plc_status_snapshot()
    }

@router.post("/close-valve", response_model=PLCCommandResponse)
async def close_valve(payload: ValveControl):
    """Closes either the inlet or outlet valve."""
    verify_adaptive_security(payload.mfa_token)
    
    cmd = "CLOSE_INLET" if payload.valve == "inlet" else "CLOSE_OUTLET"
    plant_state = simulator_service.plant.get_telemetry()
    success, detail = simulator_service.plc.process_command(cmd, plant_state)
    
    await log_event(
        event=f"PLC Close Valve ({payload.valve}) command sent",
        module="PLC",
        user="OPERATOR",
        decision="ALLOW" if success else "BLOCK",
        reason=detail,
        status="SUCCESS" if success else "FAILURE"
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
    return {
        "success": True,
        "detail": detail,
        "state": get_plc_status_snapshot()
    }

@router.post("/emergency-stop", response_model=PLCSimpleCommandResponse)
async def emergency_stop():
    """Actives the PLC Emergency Stop sequence (immediate shutdown)."""
    plant_state = simulator_service.plant.get_telemetry()
    success, detail = simulator_service.plc.process_command("EMERGENCY_STOP", plant_state)
    # Reflect new pump state immediately in physics
    simulator_service.plant.pump_status = "OFF"
    simulator_service.plant.inlet_valve_status = "CLOSED"
    
    await log_event(
        event="PLC Emergency Stop Triggered",
        module="PLC",
        user="OPERATOR",
        decision="ALLOW",
        reason="Manual operator ESTOP engagement",
        status="WARNING"
    )
    return {"success": True, "detail": detail}

@router.post("/reset-estop", response_model=PLCSimpleCommandResponse)
async def reset_estop():
    """Resets the emergency stop and clears safety trips."""
    plant_state = simulator_service.plant.get_telemetry()
    success, detail = simulator_service.plc.process_command("RESET_ESTOP", plant_state)
    
    await log_event(
        event="PLC Emergency Stop Reset",
        module="PLC",
        user="OPERATOR",
        decision="ALLOW",
        reason="Operator reset request",
        status="SUCCESS"
    )
    return {"success": True, "detail": detail}

def get_plc_status_snapshot() -> dict:
    return {
        "pump_status": simulator_service.plc.pump_status,
        "inlet_valve_status": simulator_service.plc.inlet_valve_status,
        "outlet_valve_status": simulator_service.plc.outlet_valve_status,
        **simulator_service.plc.get_state()
    }
