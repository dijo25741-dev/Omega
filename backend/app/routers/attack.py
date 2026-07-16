from fastapi import APIRouter
from app.audit.logger import log_event
from app.services.cloud_agent_bridge import send_command_to_agent
from app.services.simulator import simulator_service

router = APIRouter(prefix="/attack", tags=["Attack Simulator"])

@router.post("/reconnaissance")
@router.post("/recon")
async def simulate_reconnaissance():
    """
    Simulates network reconnaissance (port scanning, network enumeration, device discovery).
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:RECON")
    if not success:
        simulator_service.active_attack = "RECON"
        simulator_service.risk.add_risk_event("Reconnaissance: Network port scanning", 20.0)
    
    await log_event(
        event="Reconnaissance Scan Detected",
        module="COMMUNICATION",
        user="ATTACK_SIMULATOR",
        decision="MONITOR",
        reason="Port scan & network enumeration detected on subnet 192.168.10.*",
        confidence_score=0.85,
        status="WARNING"
    )
    return {
        "success": True,
        "attack": "Reconnaissance",
        "action_taken": "Network scanning alerts triggered. Asset topology updated."
    }

@router.post("/credential-theft")
@router.post("/credentials")
async def simulate_credential_theft():
    """
    Simulates brute-force credential attacks (failed logins, credential theft).
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:CREDENTIALS")
    if not success:
        simulator_service.active_attack = "CREDENTIALS"
        simulator_service.risk.add_risk_event("Brute-force credential assault", 35.0)
    
    await log_event(
        event="Brute Force Login Attack",
        module="SECURITY",
        user="ATTACK_SIMULATOR",
        decision="BLOCK",
        reason="12 failed login attempts from external IP. Credential threat detected.",
        confidence_score=0.95,
        status="FAILURE"
    )
    return {
        "success": True,
        "attack": "Credential Attack",
        "action_taken": "Lockout policies engaged. Session tokens rotated."
    }

@router.post("/lateral-movement")
@router.post("/lateral")
async def simulate_lateral_movement():
    """
    Simulates lateral movement (new device communication, suspicious remote authentication).
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:LATERAL")
    if not success:
        simulator_service.active_attack = "LATERAL"
        simulator_service.risk.add_risk_event("Lateral Movement: Suspicious RPC connection", 50.0)
    
    await log_event(
        event="Lateral Movement Detected",
        module="SECURITY",
        user="ATTACK_SIMULATOR",
        decision="BLOCK",
        reason="Unusual remote login session from internal workstation to SCADA database",
        confidence_score=0.9,
        status="FAILURE"
    )
    return {
        "success": True,
        "attack": "Lateral Movement",
        "action_taken": "Compromised device isolated. Inter-subnet rules reinforced."
    }

@router.post("/plc-command-abuse")
@router.post("/plc")
async def simulate_plc_attack():
    """
    Simulates PLC command inject attacks (STOP ALL PUMPS, CLOSE VALVES, out-of-sequence commands).
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:PLC_ATTACK")
    if not success:
        simulator_service.active_attack = "PLC_ATTACK"
        simulator_service.plc.safety_override_active = True
        simulator_service.plc.pump_status = "OFF"
        simulator_service.plc.inlet_valve_status = "CLOSED"
        simulator_service.plc.outlet_valve_status = "CLOSED"
        simulator_service.risk.add_risk_event("PLC Attack: Remote register override", 80.0)
    
    await log_event(
        event="PLC Command Injection",
        module="PLC",
        user="ATTACK_SIMULATOR",
        decision="BYPASS",
        reason="Malicious STOP PUMPS command forced direct Modbus writes bypassing safety interlocks",
        confidence_score=1.0,
        status="WARNING"
    )
    return {
        "success": True,
        "attack": "PLC Attack",
        "action_taken": "Safety trips active. Overpressure release engaged."
    }

@router.post("/ransomware")
@router.post("/malware")
async def simulate_malware():
    """
    Simulates malware / ransomware (high CPU, high disk activity, suspicious process creation).
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:MALWARE")
    if not success:
        simulator_service.active_attack = "MALWARE"
        simulator_service.risk.add_risk_event("Malware: Active file encryption payload", 90.0)
    
    await log_event(
        event="Host Malware Infection",
        module="RECOVERY",
        user="ATTACK_SIMULATOR",
        decision="CONTAIN",
        reason="High CPU usage and file encryption threads matched ransomware signatures.",
        confidence_score=0.98,
        status="FAILURE"
    )
    return {
        "success": True,
        "attack": "Malware Simulation",
        "action_taken": "Automated self-healing triggered. Re-imaging in progress."
    }

@router.post("/insider")
@router.post("/insider-threat")
async def simulate_insider_threat():
    """
    Simulates insider threat (authorized operator issuing commands outside maintenance windows).
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:INSIDER")
    if not success:
        simulator_service.active_attack = "INSIDER"
        simulator_service.risk.add_risk_event("Insider Threat: Unauthorized command executed", 30.0)
    
    await log_event(
        event="Insider Threat Alert",
        module="SECURITY",
        user="OPERATOR_ADMIN",
        decision="MONITOR",
        reason="Shutdown commands issued by authorized operator outside scheduled maintenance window.",
        confidence_score=0.8,
        status="WARNING"
    )
    return {
        "success": True,
        "attack": "Insider Threat",
        "action_taken": "Risk score elevated. Incident escalated to compliance log."
    }

@router.post("/emergency")
async def simulate_emergency():
    """
    Simulates a critical emergency by locking the workstation immediately.
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:EMERGENCY")
    if not success:
        simulator_service.active_attack = "EMERGENCY"
        await simulator_service.trigger_emergency()
    return {
        "success": True,
        "status": "Critical Emergency Forced",
        "action_taken": "Workstation locked. SCADA console input disabled."
    }

@router.post("/recovery")
async def trigger_recovery():
    """
    Simulates the self-healing recovery engine trigger.
    """
    success = await send_command_to_agent("SIMULATE_ATTACK:RECOVERY")
    if not success:
        simulator_service.active_attack = "RECOVERY"
        simulator_service.recovery.start_recovery()
    return {
        "success": True,
        "status": "Recovery Started",
        "action_taken": "Re-imaging local workstation. Restoring trusted neural state."
    }

