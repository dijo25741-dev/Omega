from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, UTC

from app.ai.threat_prediction import cni_threat_predictor
from app.ai.command_guardian import cni_command_guardian
from app.graph.graph_builder import cni_graph_manager
from app.services.simulator import simulator_service
from app.audit.logger import log_event
from app.database import async_session_maker
from app.models.ai import AIAlert
from sqlalchemy import select

router = APIRouter(prefix="/api/ai", tags=["Omega AI Core"])

class TelemetryPayload(BaseModel):
    device_id: str = Field("PLC_01", example="PUMP_01")
    device_type: Optional[str] = Field("Pump", example="Pump")
    temperature: Optional[float] = Field(60.0, example=62.4)
    pressure: Optional[float] = Field(3.5, example=4.1)
    flow: Optional[float] = Field(45.0, example=50.2)
    voltage: Optional[float] = Field(220.0, example=220.5)
    current: Optional[float] = Field(15.0, example=14.8)
    operator: Optional[str] = Field("System_Daemon", example="Operator_Admin")
    command: Optional[str] = Field(None, example="READ_STATUS")
    network_latency: Optional[float] = Field(1.8, example=2.1)
    failed_logins: Optional[int] = Field(0, example=0)
    packet_rate: Optional[float] = Field(80.0, example=85.0)
    cpu_usage: Optional[float] = Field(15.0, example=18.5)
    memory_usage: Optional[float] = Field(20.0, example=22.0)

class CommandPayload(BaseModel):
    operator: str = Field(..., example="Operator_Admin")
    command: str = Field(..., example="SHUTDOWN_PUMP")
    device_id: str = Field(..., example="PUMP_01")
    maintenance_active: Optional[bool] = Field(None, example=False)

@router.post("/predict")
def predict_threat(payload: TelemetryPayload):
    """
    Predicts the current cyber attack stage based on telemetry parameters.
    """
    return cni_threat_predictor.predict_threat_stage(payload.model_dump())

@router.post("/validate-command")
async def validate_operator_command(payload: CommandPayload):
    """
    Intercepts operator control commands and runs security context validation checks.
    """
    # Fetch active plant physics parameters
    current_telemetry = {
        "temperature": 58.0,
        "pressure": simulator_service.plant.pressure,
        "flow": simulator_service.plant.flow_rate
    }
    
    # Predict active threat stage
    threat_details = cni_threat_predictor.predict_threat_stage(current_telemetry)
    predicted_stage = threat_details["predicted_attack"]
    
    # Run Guardian
    verdict = cni_command_guardian.evaluate_command(
        operator=payload.operator,
        command=payload.command,
        device_id=payload.device_id,
        current_telemetry=current_telemetry,
        predicted_threat_stage=predicted_stage,
        maintenance_active=payload.maintenance_active
    )
    
    # Log execution result to SQL audits
    await log_event(
        event="Operator Control Validation",
        module="AI_GUARDIAN",
        user=payload.operator,
        decision=verdict["decision"],
        reason=verdict["reason"],
        confidence_score=verdict["confidence"] / 100.0,
        status="SUCCESS" if verdict["allowed"] else "FAILURE"
    )
    
    # Override PLC values if allowed and it is a control command
    if verdict["allowed"]:
        if payload.command == "START_PUMP":
            simulator_service.plc.pump_status = "ON"
        elif payload.command == "SHUTDOWN_PUMP":
            simulator_service.plc.pump_status = "OFF"
        elif payload.command == "OPEN_VALVE":
            simulator_service.plc.inlet_valve_status = "OPEN"
        elif payload.command == "CLOSE_VALVE":
            simulator_service.plc.inlet_valve_status = "CLOSED"
            
    return verdict

@router.get("/explanation")
def get_latest_explanation():
    """
    Returns the latest explainability decision package, highlighting security alerts,
    SHAP attributions, waterfall plots, and active mitigating playbooks.
    """
    exp = getattr(simulator_service, "latest_ai_explanation", {})
    if not exp:
        return {
            "decision": "MONITORING",
            "summary": "No threat decision calculated yet.",
            "details": ["Telemetry monitor active."],
            "threat_stage": "Normal",
            "risk_score": 0.0,
            "confidence": 100.0,
            "shap_attributions": {},
            "shap_chart_base64": "",
            "incident_playbook": {}
        }
    return exp

@router.get("/graph")
def get_network_graph():
    """
    Returns NetworkX critical asset topology node and edge mapping.
    """
    return cni_graph_manager.get_graph_dict()

@router.post("/retrain")
async def trigger_retraining():
    """
    Gathers historical database records and triggers retraining of threat model.
    """
    async with async_session_maker() as session:
        # Fetch recent alerts to use as training labels
        result = await session.execute(
            select(AIAlert).order_by(AIAlert.id.desc()).limit(200)
        )
        rows = result.scalars().all()
        
    records = []
    for r in rows:
        records.append({
            "network_latency": 2.0,
            "failed_logins": 5 if r.threat_stage == "Credential Theft" else 0,
            "packet_rate": 600.0 if r.threat_stage == "Ransomware" else 100.0,
            "cpu_usage": 90.0 if r.threat_stage == "Ransomware" else 20.0,
            "memory_usage": 80.0 if r.threat_stage == "Ransomware" else 30.0,
            "is_anomaly": 1 if r.risk_level in ["High", "Critical"] else 0,
            "command": "ENCRYPT" if r.threat_stage == "Ransomware" else "READ"
        })
        
    success = cni_threat_predictor.retrain_model_from_db(records)
    if not success:
        raise HTTPException(status_code=400, detail="Retraining failed. DB might be cold.")
    return {"message": "Random Forest model retrained and serialized."}

@router.get("/dashboard")
def get_dashboard_metrics():
    """
    Provides unified JSON payload of active plant physics and AI cybersecurity stats.
    """
    exp = getattr(simulator_service, "latest_ai_explanation", {})
    return {
        "plant_metrics": {
            "water_level": simulator_service.plant.water_level,
            "pressure": simulator_service.plant.pressure,
            "flow_rate": simulator_service.plant.flow_rate,
            "pump_status": simulator_service.plc.pump_status,
            "inlet_valve_status": simulator_service.plc.inlet_valve_status,
            "outlet_valve_status": simulator_service.plc.outlet_valve_status
        },
        "security_posture": simulator_service.security.get_state(),
        "active_communication": simulator_service.comms.get_state(),
        "ai_brain": {
            "threat_stage": exp.get("threat_stage", "Normal"),
            "risk_score": exp.get("risk_score", 0.0),
            "risk_level": exp.get("risk_level", "Low"),
            "confidence": exp.get("confidence", 100.0),
            "raw_text": exp.get("raw_text", ""),
            "shap_chart_base64": exp.get("shap_chart_base64", ""),
            "incident_playbook": exp.get("incident_playbook", {})
        },
        "device_graph": cni_graph_manager.get_graph_dict(),
        "system_status": {
            "uptime_seconds": int((datetime.now(UTC) - simulator_service.start_time).total_seconds()) if getattr(simulator_service, "start_time", None) else 0,
            "simulation_mode": simulator_service.active_attack,
            "self_healing": simulator_service.recovery.get_state()
        }
    }
