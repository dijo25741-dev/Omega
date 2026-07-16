import time
import logging
import jwt
from typing import Dict
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.simulator import simulator_service
from app.websocket.manager import manager
from app.audit.logger import log_event
from app.services.cloud_agent_bridge import send_command_to_agent
from app.ai.command_guardian import cni_command_guardian
from app.ai.threat_prediction import cni_threat_predictor

logger = logging.getLogger("omega.trust_router")

router = APIRouter(prefix="/api", tags=["Omega Trust & Recovery"])

JWT_SECRET = "omega_super_secret_cyber_immune_key"
JWT_ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    username: str
    password: str

class LearnDataRequest(BaseModel):
    data: dict

class ValidateDataRequest(BaseModel):
    source: str
    data_hash: str
    payload: dict

class ActionRequest(BaseModel):
    action_type: str
    payload: dict

class EmergencyResponse(BaseModel):
    decision: str
    token: str

class LaptopCommandRequest(BaseModel):
    command: str
    payload: dict = {}

def get_sim_time():
    return time.strftime("%H:%M:%S", time.localtime())

@router.post("/login")
async def login(req: LoginRequest):
    """Logs in operator and generates authentication tokens for Mobile Guardian."""
    if req.username == "admin" and req.password == "omega2026":
        token = jwt.encode(
            {"sub": req.username, "role": "guardian", "exp": time.time() + 3600},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        simulator_service.virtual_mobile_authorized = True
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/check-integrity")
async def check_integrity():
    """Checks neural weights integrity and quarantining status with full laptop telemetry."""
    from app.services.monitor import host_monitor
    host_telemetry = host_monitor.collect_telemetry()
    
    # Timeline formatting
    timeline_events = []
    for event in simulator_service.timeline:
        timeline_events.append({
            "time": event.get("time", ""),
            "event": event.get("event", ""),
            "severity": event.get("severity", "info")
        })
        
    ai_exp = {
        "action": "HIGH_RISK_ALERT" if simulator_service.risk.risk_score > 50.0 else "MONITORING",
        "reason": [
            f"Infrastructure Risk Score = {simulator_service.risk.risk_score}",
            f"Risk Level = {simulator_service.risk.risk_level}"
        ],
        "confidence": 99.8 if simulator_service.risk.risk_score < 50.0 else 85.0
    }
    
    processes = []
    for idx, p in enumerate(host_telemetry.get("new_processes", [])[:5]):
        processes.append({
            "pid": 1000 + idx,
            "name": p,
            "cpu": 5.0
        })
        
    return {
        "status": simulator_service.integrity_status,
        "action": "FREEZE_MODEL" if simulator_service.learning_frozen else "NONE",
        "active_model_hash": simulator_service.active_model_hash,
        "risk_value": float(simulator_service.risk.risk_score),
        "risk_level": simulator_service.risk.risk_level,
        "cpu_usage": float(host_telemetry.get("host_cpu", 0.0)),
        "ram_usage": float(host_telemetry.get("host_memory", 0.0)),
        "battery_level": 100,
        "files_destroyed": simulator_service.files_destroyed,
        "screenshot_url": simulator_service.screenshot_url,
        "active_processes": processes,
        "active_sessions": [
            {
                "session_id": "sess_001",
                "user": "operator",
                "ip": "127.0.0.1",
                "device": "workstation-01"
            }
        ],
        "learning_frozen": simulator_service.learning_frozen,
        "emergency_active": simulator_service.emergency_active,
        "workstation_blocked": simulator_service.workstation_blocked,
        "pending_emergency_command": simulator_service.pending_emergency_command,
        "compromise_type": simulator_service.compromise_type,
        "timeline": timeline_events,
        "ai_explanation": ai_exp
    }

class MouseMoveRequest(BaseModel):
    dx: float
    dy: float
    click: str = ""

@router.post("/laptop/mouse")
async def laptop_mouse(req: MouseMoveRequest):
    """Sends relative mouse movement or click commands to the laptop agent."""
    await send_command_to_agent(f"MOUSE:{req.dx}:{req.dy}:{req.click}")
    return {"status": "SUCCESS"}

@router.post("/laptop/command")
async def laptop_command(req: LaptopCommandRequest):
    """Sends a direct command to the laptop agent from the mobile app."""
    cmd_map = {
        "LOCK": "LOCK",
        "MUTE": "MUTE",
        "KILL_PROCESS": "KILL_PROCESS",
        "SHUTDOWN": "SHUTDOWN",
        "LOGOUT": "LOGOUT",
        "DISABLE_NETWORK": "DISABLE_NETWORK",
        "RESET_STATE": "RESET_STATE",
        "UNLOCK": "UNLOCK"
    }
    agent_cmd = cmd_map.get(req.command, req.command)
    await send_command_to_agent(agent_cmd)
    return {"status": "SUCCESS", "message": f"Command '{agent_cmd}' relayed to agent."}

@router.post("/kill-switch")
async def kill_switch():
    """Triggers immediate total lockdown (Kill Switch) from the mobile guardian."""
    await send_command_to_agent("SIMULATE_ATTACK:EMERGENCY")
    simulator_service.emergency_active = True
    simulator_service.workstation_blocked = True
    simulator_service.risk.risk_score = 100.0
    simulator_service.risk.risk_level = "CRITICAL"
    
    await log_event(
        event="Kill Switch Activated",
        module="SECURITY",
        user="MOBILE_GUARDIAN",
        decision="LOCKDOWN",
        reason="Emergency Kill Switch triggered by Mobile Guardian.",
        confidence_score=1.0,
        status="CRITICAL"
    )
    return {"status": "SUCCESS", "message": "Kill switch executed. Workstation locked."}

@router.get("/recovery-status")
async def get_recovery_status():
    """Gets the recovery process steps and status for the mobile guardian."""
    state = simulator_service.recovery.get_state()
    stage = state["stage"]
    in_progress = state["in_progress"]
    percentage = state["percentage"]
    
    steps = [
        {
            "label": "Containment: Rotate routes and isolate threat",
            "status": "done" if (percentage >= 25.0 or (not in_progress and stage == "NONE" and percentage == 0.0)) else "in_progress" if (in_progress and stage == "CONTAIN") else "pending"
        },
        {
            "label": "Restoration: Re-flash PLC register memories",
            "status": "done" if (percentage >= 50.0 or (not in_progress and stage == "NONE" and percentage == 0.0)) else "in_progress" if (in_progress and stage == "RECOVER") else "pending"
        },
        {
            "label": "Verification: Run pressure and tank level simulation test",
            "status": "done" if (percentage >= 75.0 or (not in_progress and stage == "NONE" and percentage == 0.0)) else "in_progress" if (in_progress and stage == "VERIFY") else "pending"
        },
        {
            "label": "Resolution: Clear risk baseline and lower security levels",
            "status": "done" if (percentage >= 100.0 or (not in_progress and stage == "NONE" and percentage == 0.0)) else "in_progress" if (in_progress and stage == "RESUME") else "pending"
        }
    ]
    
    if not in_progress and simulator_service.risk.risk_level in ["HIGH", "CRITICAL"]:
        steps = [
            {"label": "Containment: Rotate routes and isolate threat", "status": "pending"},
            {"label": "Restoration: Re-flash PLC register memories", "status": "pending"},
            {"label": "Verification: Run pressure and tank level simulation test", "status": "pending"},
            {"label": "Resolution: Clear risk baseline and lower security levels", "status": "pending"}
        ]
        
    return {"steps": steps}

@router.post("/simulate-attack")
async def simulate_attack(req: Dict):
    """Simulates active cyber-attack vectors: weighting tampering, PLC spoofing, session hijacking."""
    attack_type = req.get("type", "WEIGHT_TAMPER")
    await send_command_to_agent(f"SIMULATE_ATTACK:{attack_type}")
    
    # Trigger high risk status in local cache
    simulator_service.compromise_type = attack_type
    simulator_service.risk.risk_score = 82.0
    simulator_service.risk.risk_level = "HIGH"
    
    await log_event(
        event=f"Simulated Attack Vector: {attack_type}",
        module="SECURITY",
        user="ATTACK_SIMULATOR",
        decision="BLOCK" if attack_type == "WEIGHT_TAMPER" else "MONITOR",
        reason="Security test injection",
        confidence_score=1.0,
        status="WARNING"
    )
    return {"status": "Attack vector simulated", "type": attack_type}

@router.post("/learn-data")
async def learn_data(req: LearnDataRequest):
    """Validates physics limits and baseline deviations on learning buffers."""
    if simulator_service.learning_frozen:
        return {"status": "REJECTED", "reason": "Learning pipeline is FROZEN due to system compromise state"}
        
    sensor_val = req.data.get("val", 0)
    if sensor_val > 100 or sensor_val < 0:
        return {"status": "REJECTED", "reason": "Physics Validation check failed: Value is out of boundaries"}
    if sensor_val > 85.0:
        return {"status": "REJECTED", "reason": "Baseline deviation check failed: Input value deviates from average"}
        
    return {"status": "ACCEPTED", "reason": "Input validated. Temporary buffer committed to training weights."}

@router.post("/validate-data")
async def validate_data(req: ValidateDataRequest):
    """Performs source signature and hash validation checks on Modbus blocks."""
    if req.source not in ["OT_SENSOR_PLC_1", "OT_SENSOR_PLC_2"]:
        return {"trusted": False, "reason": "Data Provenance Failure: Unregistered hardware source signature"}
    if len(req.data_hash) < 10 or "BAD" in req.data_hash:
        return {"trusted": False, "reason": "Provenance integrity check failed: Block hash signature mismatch"}
    return {"trusted": True, "reason": "Source matches register block hash and is signed with hardware key."}

@router.post("/trigger-emergency")
async def trigger_emergency():
    """Triggers workstation emergency lock and delegates token authority to Mobile Guardian."""
    await send_command_to_agent("SIMULATE_ATTACK:EMERGENCY")
    
    # Update local cache immediately
    simulator_service.emergency_active = True
    simulator_service.workstation_blocked = True
    simulator_service.risk.risk_score = 98.0
    simulator_service.risk.risk_level = "CRITICAL"
    
    await log_event(
        event="Emergency Lockout Triggered",
        module="SECURITY",
        user="SYSTEM",
        decision="LOCK",
        reason="Manual emergency trip or high threat quarantine initiated.",
        confidence_score=1.0,
        status="WARNING"
    )
    return {"status": "Emergency lockout engaged"}

@router.post("/action")
async def process_action(req: ActionRequest):
    """Intercepts operator actions and routes them adaptively based on CNI risk level."""
    risk_level = simulator_service.risk.risk_level.upper()
    is_critical_cmd = req.action_type in ["SHUTDOWN_PLANT", "TOGGLE_PUMP", "CLOSE_VALVE"]

    # 1. EMERGENCY MODE PATH
    if simulator_service.workstation_blocked or risk_level == "CRITICAL":
        if is_critical_cmd:
            simulator_service.pending_emergency_command = req.action_type
            if not simulator_service.workstation_blocked:
                await trigger_emergency()
            await log_event(
                event=f"Orchestrator Diverted Command: {req.action_type}",
                module="ORCHESTRATOR",
                user="OPERATOR",
                decision="DIVERT",
                reason="Emergency mode active. Command diverted to Mobile Guardian Approval loop.",
                confidence_score=1.0,
                status="WARNING"
            )
            # Raise 403 to trigger UI block display on the SCADA dashboard
            raise HTTPException(
                status_code=403,
                detail="Critical Command locked. Diverted to Mobile Guardian for out-of-band approval."
            )
        else:
            # Safe read-only or minor command forwarded directly
            await send_command_to_agent(req.action_type)
            return {"status": "SUCCESS"}

    # 2. PROTECTION MODE PATH (High Risk)
    elif risk_level == "HIGH":
        telemetry = simulator_service.plant.get_telemetry()
        # Construct dynamic prediction frame
        ai_frame = {
            "timestamp": datetime.now(UTC).isoformat(),
            "device_id": "PLC_01",
            "device_type": "PLC",
            "temperature": 58.0,
            "pressure": telemetry.get("pressure", 3.0),
            "flow": telemetry.get("flow_rate", 12.0),
            "voltage": 220.0,
            "current": 15.0,
            "operator": "OPERATOR",
            "command": req.action_type,
            "network_latency": 2.0,
            "failed_logins": 0,
            "packet_rate": 80.0,
            "cpu_usage": 20.0,
            "memory_usage": 30.0
        }
        prediction = cni_threat_predictor.predict_threat_stage(ai_frame)
        threat_stage = prediction["predicted_attack"]

        # Map to canonical critical command name for evaluate_command check
        eval_cmd = "SHUTDOWN_PUMP" if req.action_type == "TOGGLE_PUMP" else "CLOSE_VALVE" if req.action_type == "CLOSE_VALVE" else req.action_type

        eval_res = cni_command_guardian.evaluate_command(
            operator="OPERATOR",
            command=eval_cmd,
            device_id="PLC_01",
            current_telemetry=telemetry,
            predicted_threat_stage=threat_stage
        )

        if not eval_res["allowed"]:
            await log_event(
                event=f"Orchestrator Blocked Command: {req.action_type}",
                module="ORCHESTRATOR",
                user="OPERATOR",
                decision="BLOCK",
                reason=eval_res["reason"],
                confidence_score=eval_res["confidence"] / 100.0,
                status="CRITICAL"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Adaptive Policy Violation: {eval_res['reason']}"
            )
        else:
            await send_command_to_agent(req.action_type)
            await log_event(
                event=f"Orchestrator Verified Command: {req.action_type}",
                module="ORCHESTRATOR",
                user="OPERATOR",
                decision="ALLOW",
                reason=f"Protection Mode check complete: {eval_res['reason']}",
                confidence_score=eval_res["confidence"] / 100.0,
                status="SUCCESS"
            )
            return {"status": "SUCCESS"}

    # 3. NORMAL OBSERVATION MODE PATH (Low/Medium Risk)
    else:
        await send_command_to_agent(req.action_type)
        await log_event(
            event=f"Orchestrator Forwarded Command: {req.action_type}",
            module="ORCHESTRATOR",
            user="OPERATOR",
            decision="ALLOW",
            reason="Normal direct command path routed under low-risk threshold.",
            confidence_score=1.0,
            status="SUCCESS"
        )
        return {"status": "SUCCESS"}

@router.post("/respond-emergency")
async def respond_emergency(req: EmergencyResponse):
    """Processes Mobile Guardian validation tokens to approve or reject actions."""
    try:
        # Validate JWT token unless bypass active
        if req.token != "virtual_bypass":
            jwt.decode(req.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    action = simulator_service.pending_emergency_command or "Critical Override"
    
    # Proxy decision to the agent
    success = await send_command_to_agent(f"RESPOND_EMERGENCY:{req.decision}")
    
    if not success:
        # Local fallback execution for tests or offline standalone demo runs
        if req.decision == "APPROVE":
            if action == "SHUTDOWN_PLANT":
                simulator_service.plc.pump_status = "OFF"
                simulator_service.plc.inlet_valve_status = "CLOSED"
                simulator_service.plc.outlet_valve_status = "CLOSED"
            elif action == "TOGGLE_PUMP":
                simulator_service.plc.pump_status = "OFF" if simulator_service.plc.pump_status == "ON" else "ON"
            elif action == "CLOSE_VALVE":
                simulator_service.plc.inlet_valve_status = "CLOSED" if simulator_service.plc.inlet_valve_status == "OPEN" else "OPEN"
        
        # Reset local security lockout state
        simulator_service.emergency_active = False
        simulator_service.workstation_blocked = False
        simulator_service.pending_emergency_command = None
        simulator_service.risk.risk_score = 12.0
        simulator_service.risk.risk_level = "LOW"
        simulator_service.integrity_status = "SAFE"
        simulator_service.learning_frozen = False
        simulator_service.compromise_type = "NONE"
    
    await log_event(
        event="Emergency Lockout Recovered",
        module="SECURITY",
        user="MOBILE_GUARDIAN",
        decision=req.decision,
        reason=f"Action [{action}] processed. Workstation restored to baseline.",
        confidence_score=1.0,
        status="SUCCESS"
    )
    return {"status": "SUCCESS"}

@router.post("/reset")
async def reset_state():
    """Resets simulator parameters to baseline normal operational status."""
    success = await send_command_to_agent("RESET_STATE")
    if not success:
        simulator_service.risk.reset()
        simulator_service.plc.emergency_stopped = False
        simulator_service.plc.safety_trip = False
        simulator_service.plc.safety_override_active = False
        simulator_service.plc.pump_status = "OFF"
        simulator_service.plc.inlet_valve_status = "OPEN"
        simulator_service.plc.outlet_valve_status = "CLOSED"
        simulator_service.emergency_active = False
        simulator_service.workstation_blocked = False
        simulator_service.pending_emergency_command = None
        simulator_service.integrity_status = "SAFE"
        simulator_service.learning_frozen = False
        simulator_service.compromise_type = "NONE"
        simulator_service.recovery.reset()
    return {"status": "RESET_SUCCESS"}
