import asyncio
import logging
import random
from datetime import datetime, UTC
from sqlalchemy import select
from app.plant.plant_simulator import WaterTreatmentPlantSimulator
from app.plc.plc_controller import PLCController
from app.communication.orchestrator import CommunicationOrchestrator
from app.security.security_engine import SecurityEngine
from app.services.risk_engine import RiskEngine
from app.services.recovery_engine import RecoveryEngine
from app.websocket.manager import manager
from app.database import async_session_maker
from app.models.plant import PlantState
from app.models.plc import PLCState
from app.models.communication import CommunicationState
from app.models.security import SecurityState
from app.models.risk import RiskState
from app.models.recovery import RecoveryState
from app.models.ai import AIAlert
from app.audit.logger import log_event

# AI Core Imports
from app.ai.infrastructure_learning import cni_behavior_learner
from app.ai.threat_prediction import cni_threat_predictor
from app.ai.risk_engine import cni_risk_engine
from app.ai.explainable_ai import cni_explainable_ai
from app.graph.graph_builder import cni_graph_manager

logger = logging.getLogger("omega.simulator")

class SimulatorService:
    """
    Coordinates the background simulation cycle.
    Updates telemetry, checks rules, runs risk analysis, rotates routes,
    manages auto-recovery, writes logs to DB, and pushes WebSocket events.
    """
    def __init__(self):
        self.plant = WaterTreatmentPlantSimulator()
        self.plc = PLCController()
        self.comms = CommunicationOrchestrator()
        self.security = SecurityEngine()
        self.risk = RiskEngine()
        self.recovery = RecoveryEngine()
        self._running = False
        self._task = None
        
        self.active_attack = "NONE"
        self.latest_ai_explanation = {}
        self.start_time = datetime.now(UTC)
        
        # Member 3 Trust & Recovery states
        self.integrity_status = "SAFE"
        self.learning_frozen = False
        self.active_model_hash = "sha256_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        self.trusted_snapshot = "sha256_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        self.emergency_active = False
        self.workstation_blocked = False
        self.pending_emergency_command = None
        self.compromise_type = "NONE"
        self.screenshot_url = "/static/placeholder.png"
        self.files_destroyed = False
        self.timeline = [
            {"time": "17:00:00", "event": "Cyber-immune core v2.0 initialized", "severity": "info"},
            {"time": "17:05:00", "event": "Model signature matching baseline: Verified", "severity": "info"}
        ]
        self.virtual_mobile_authorized = False

    async def trigger_emergency(self):
        """Triggers workstation emergency lock and delegates token authority to Mobile Guardian."""
        self.emergency_active = True
        self.workstation_blocked = True
        self.risk.risk_score = 98.0
        self.risk.risk_level = "CRITICAL"
        
        # Add to timeline if not duplicate
        now_str = datetime.now().strftime("%H:%M:%S")
        self.timeline.append({
            "time": now_str,
            "event": "CYBER-IMMUNITY ENGAGED: Workstation lockout triggered. Mobile Guardian bind requested.",
            "severity": "critical"
        })
        
        await log_event(
            event="Emergency Lockout Triggered",
            module="SECURITY",
            user="SYSTEM",
            decision="LOCK",
            reason="Manual emergency trip or high threat quarantine initiated.",
            confidence_score=1.0,
            status="WARNING"
        )

    async def start(self):
        """Starts the simulator task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Simulator Service task started.")

    async def stop(self):
        """Stops the simulator task."""
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Simulator Service task stopped.")

    async def _loop(self):
        while self._running:
            try:
                # 1. Align Physical Plant state with PLC output registers
                self.plant.pump_status = self.plc.pump_status
                self.plant.inlet_valve_status = self.plc.inlet_valve_status
                self.plant.outlet_valve_status = self.plc.outlet_valve_status

                # 2. Advance plant physics by 1 second
                telemetry = self.plant.step()

                # 3. Execute PLC safety rules loop
                safety_tripped, safety_msg = self.plc.run_safety_checks(self.plant)
                if safety_tripped:
                    # Sync registers to reflect forced safety shutdown
                    self.plc.pump_status = self.plant.pump_status
                    self.plc.inlet_valve_status = self.plant.inlet_valve_status
                    
                    await log_event(
                        event="PLC Safety Trip Active",
                        module="PLC",
                        user="SYSTEM",
                        decision="TRIP",
                        reason=safety_msg,
                        confidence_score=1.0,
                        status="WARNING"
                    )

                # 4. Extract real host background monitor telemetry & update based on active attack states
                from app.services.monitor import host_monitor
                host_telemetry = host_monitor.collect_telemetry()
                
                active_att = getattr(self, "active_attack", "NONE")
                
                # Baseline from real host
                cpu_usage = host_telemetry["host_cpu"]
                memory_usage = host_telemetry["host_memory"]
                failed_logins = host_telemetry["failed_logins"]
                packet_rate = 80.0 + random.uniform(-5.0, 5.0)
                network_latency = 1.8 + random.uniform(-0.3, 0.3)
                outbound_connections = host_telemetry["outbound_connections"]
                
                operator = "System_Daemon"
                command = "READ_STATUS"
                device_id = "PLC_01"
                
                # Check for active attack overlays
                if active_att in ["RECONNAISSANCE", "RECON"]:
                    packet_rate = 320.0 + random.uniform(-20.0, 20.0)
                    network_latency = 4.8 + random.uniform(-0.5, 0.5)
                    operator = "Nmap_Scanner"
                    command = "PORT_SCAN"
                    if "nmap.exe (PID: 9999)" not in host_monitor.new_processes_detected:
                        host_monitor.new_processes_detected = ["nmap.exe (PID: 9999)"] + host_monitor.new_processes_detected
                elif active_att in ["CREDENTIAL_THEFT", "CREDENTIALS"]:
                    failed_logins = max(failed_logins, random.randint(8, 15))
                    host_monitor.failed_logins = failed_logins
                    packet_rate = 240.0 + random.uniform(-15.0, 15.0)
                    operator = "Hydra_Brute"
                    command = "SSH_LOGIN"
                elif active_att in ["LATERAL", "LATERAL_MOVEMENT"]:
                    outbound_connections += random.randint(5, 12)
                    operator = "Remote_Admin"
                    command = "REMOTE_EXEC"
                    device_id = "SCADA_01"
                elif active_att in ["PLC_COMMAND_ABUSE", "PLC_ATTACK"]:
                    operator = "Malicious_Actor"
                    command = "STOP_ALL_PUMPS"
                    device_id = "PUMP_01"
                    # Force shut down pumps
                    self.plc.pump_status = "OFF"
                    self.plc.inlet_valve_status = "CLOSED"
                    self.plc.outlet_valve_status = "CLOSED"
                elif active_att in ["RANSOMWARE", "MALWARE"]:
                    cpu_usage = 92.5 + random.uniform(-2.0, 2.0)
                    memory_usage = 89.0 + random.uniform(-2.0, 2.0)
                    network_latency = 22.0 + random.uniform(-2.0, 2.0)
                    operator = "LockBit_Agent"
                    command = "ENCRYPT_FILES"
                    device_id = "DB_01"
                    
                    # Trigger some file modification alerts in monitor
                    if "MODIFIED: config.db.locked" not in host_monitor.file_changes_detected:
                        host_monitor.file_changes_detected = ["MODIFIED: config.db.locked", "CREATED: README_TO_DECRYPT.txt"] + host_monitor.file_changes_detected
                    if "ransomware_encryptor.exe (PID: 11223)" not in host_monitor.new_processes_detected:
                        host_monitor.new_processes_detected = ["ransomware_encryptor.exe (PID: 11223)"] + host_monitor.new_processes_detected
                elif active_att in ["INSIDER", "INSIDER_THREAT"]:
                    operator = "Operator_Admin" # Authorized operator
                    command = "DISABLE_SAFETY_LIMIT" # Unusual command
                    device_id = "PLC_01"
                    
                # Create telemetry frame to supply to AI Brain
                ai_frame = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "device_id": device_id,
                    "device_type": "Pump" if "PUMP" in device_id else "Valve" if "VALVE" in device_id else "PLC",
                    "temperature": 88.0 + random.uniform(-2.0, 2.0) if active_att in ["PLC_COMMAND_ABUSE", "PLC_ATTACK"] else 58.0 + random.uniform(-2.0, 2.0),
                    "pressure": telemetry["pressure"],
                    "flow": telemetry["flow_rate"],
                    "voltage": 220.0 + random.uniform(-4.0, 4.0),
                    "current": 15.0 + random.uniform(-1.0, 1.0),
                    "operator": operator,
                    "command": command,
                    "network_latency": network_latency,
                    "failed_logins": failed_logins,
                    "packet_rate": packet_rate,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage
                }

                # 5. Run AI Cyber Immune Systems calculations
                cni_behavior_learner.learn_telemetry_frame(ai_frame)
                is_anom, max_z, deviations = cni_behavior_learner.evaluate_telemetry_anomaly(ai_frame)
                
                prediction = cni_threat_predictor.predict_threat_stage(ai_frame)
                threat = prediction["predicted_attack"]
                conf = prediction["confidence"]
                
                op_trust = cni_behavior_learner.operator_trust[operator]
                dev_trust = cni_behavior_learner.device_trust[device_id]
                
                risk_data = cni_risk_engine.calculate_risk(
                    threat_prediction=threat,
                    threat_confidence=conf,
                    anomaly_score=max_z,
                    device_trust=dev_trust,
                    operator_trust=op_trust,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    network_latency=network_latency
                )
                
                # Sync AI computed risk with simulator baseline
                self.risk.risk_score = risk_data["risk_score"]
                self.risk.risk_level = risk_data["risk_level"].upper()
                risk_state = self.risk.get_state()

                # Generate detailed explanation package
                explanation = cni_explainable_ai.generate_explanation(
                    decision="HIGH_RISK_ALERT" if risk_data["risk_level"] in ["High", "Critical"] else "MONITORING",
                    threat_stage=threat,
                    risk_score=risk_data["risk_score"],
                    confidence=conf,
                    operator=operator,
                    command=command,
                    device_id=device_id,
                    anomalies={k: v for k, v in deviations.items() if v > 3.0},
                    telemetry=ai_frame
                )
                explanation["chart_base64"] = cni_explainable_ai.generate_contribution_chart(risk_data["metrics"])
                self.latest_ai_explanation = explanation

                # Update live topological node layouts
                node_status = "HEALTHY"
                if risk_data["risk_level"] == "Medium" or is_anom:
                    node_status = "ANOMALOUS"
                elif risk_data["risk_level"] in ["High", "Critical"]:
                    node_status = "ATTACKED"
                cni_graph_manager.update_node_status(device_id, node_status, trust_score=dev_trust)

                # 6. Adapt communication routes and security rules based on risk levels
                sec_state = self.security.get_state()
                if sec_state["level"] != risk_state["risk_level"]:
                    sec_update = self.security.adapt_to_risk(risk_state["risk_level"])
                    for change in sec_update["changes"]:
                        await log_event(
                            event="Security Posture Adapted",
                            module="SECURITY",
                            user="RISK_ENGINE",
                            decision="UPDATE",
                            reason=change,
                            confidence_score=0.9,
                            status="WARNING" if risk_state["risk_level"] in ["HIGH", "CRITICAL"] else "SUCCESS"
                        )

                rotated = self.comms.adapt_to_risk(risk_state["risk_level"])
                if rotated:
                    await log_event(
                        event="Communication Route Rotated",
                        module="COMMUNICATION",
                        user="RISK_ENGINE",
                        decision="ROTATE",
                        reason=f"Risk score elevated. Internal route shifted to {self.comms.get_active_route()}",
                        confidence_score=0.95,
                        status="SUCCESS"
                    )

                # 7. Step the self-healing recovery system if active
                if self.recovery.in_progress:
                    recovery_stepped, recovery_msg = self.recovery.step(
                        self.plant, self.plc, self.comms, self.security, self.risk
                    )
                    if recovery_stepped and recovery_msg:
                        # Sync registers from recovery updates
                        self.plc.pump_status = self.plant.pump_status
                        self.plc.inlet_valve_status = self.plant.inlet_valve_status
                        self.plc.outlet_valve_status = self.plant.outlet_valve_status
                        
                        await log_event(
                            event="Recovery Action Run",
                            module="RECOVERY",
                            user="RECOVERY_ENGINE",
                            decision="RESTORE",
                            reason=recovery_msg,
                            confidence_score=1.0,
                            status="SUCCESS"
                        )

                # 8. Persist metrics snapshot into database tables
                await self._persist_states()

                # 9. Broadcast consolidated state update to WebSockets
                payload = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "plant": telemetry,
                    "plc": {
                        "pump_status": self.plc.pump_status,
                        "inlet_valve_status": self.plc.inlet_valve_status,
                        "outlet_valve_status": self.plc.outlet_valve_status,
                        **self.plc.get_state()
                    },
                    "communication": self.comms.get_state(),
                    "security": self.security.get_state(),
                    "risk": risk_state,
                    "recovery": self.recovery.get_state(),
                    "ai_intelligence": explanation,
                    "device_graph": cni_graph_manager.get_graph_dict()
                }
                await manager.broadcast(payload)
                
                # Broadcast payload for Member 3/React Dashboard
                react_payload = {
                    "type": "TELEMETRY",
                    "data": {
                        "risk_level": self.risk.risk_level,
                        "risk_value": int(self.risk.risk_score),
                        "pump_status": self.plc.pump_status,
                        "valve_status": self.plc.inlet_valve_status,
                        "tank_level": round(self.plant.water_level, 2),
                        "flow_rate": round(self.plant.flow_rate, 2),
                        "integrity_status": self.integrity_status,
                        "learning_frozen": self.learning_frozen,
                        "active_model_hash": self.active_model_hash,
                        "emergency_active": self.emergency_active,
                        "workstation_blocked": self.workstation_blocked,
                        "pending_emergency_command": self.pending_emergency_command,
                        "compromise_type": self.compromise_type,
                        "timeline": self.timeline,
                        "ai_explanation": {
                            "action": explanation.get("decision", "MONITORING"),
                            "reason": explanation.get("details", ["Operating normal"]),
                            "confidence": explanation.get("confidence", 99.8)
                        },
                        "host_monitor": host_telemetry
                    }
                }
                await manager.broadcast(react_payload)
                
                # 10. Handle decay or resetting of active attack scenarios
                self.compromise_type = active_att
                if self.recovery.in_progress:
                    self.active_attack = "MALWARE"
                elif active_att in ["MALWARE", "RANSOMWARE"] and not self.recovery.in_progress:
                    self.active_attack = "NONE"
                elif active_att in ["RECONNAISSANCE", "RECON", "CREDENTIAL_THEFT", "CREDENTIALS", "LATERAL", "LATERAL_MOVEMENT", "PLC_COMMAND_ABUSE", "PLC_ATTACK", "COMMUNICATION_DISRUPTION", "INSIDER", "INSIDER_THREAT"]:
                    # Instantaneous simulation sweeps decay after 1 step
                    self.active_attack = "NONE"

                # 11. Emergency Mode Lockout Check
                if self.risk.risk_score > 75.0 and not self.workstation_blocked:
                    await self.trigger_emergency()

                # 12. Automated Recovery check
                if self.active_attack == "NONE" and not self.recovery.in_progress and self.workstation_blocked and not self.emergency_active:
                    self.emergency_active = False
                    self.workstation_blocked = False
                    self.pending_emergency_command = None
                    self.risk.risk_score = 12.0
                    self.risk.risk_level = "LOW"
                    self.integrity_status = "SAFE"
                    self.learning_frozen = False
                    self.compromise_type = "NONE"
                    
                    self.timeline.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "event": "AUTOMATIC RECOVERY: Threat signatures subsided. SCADA console unlocked.",
                        "severity": "info"
                    })
                    
                    await log_event(
                        event="Automatic Lockout Recovery",
                        module="SECURITY",
                        user="SYSTEM",
                        decision="UNLOCK",
                        reason="Threat signatures normalized. Access controls restored.",
                        confidence_score=1.0,
                        status="SUCCESS"
                    )
                    await manager.broadcast({"type": "RECOVERY_COMPLETE"})

            except Exception as e:
                logger.error(f"Error in background simulator loop: {e}", exc_info=True)

            await asyncio.sleep(1.0)

    async def _persist_states(self):
        """Asynchronously writes a snapshot of current module parameters to DB."""
        async with async_session_maker() as session:
            try:
                now = datetime.now(UTC)
                
                # PlantState
                plant_db = PlantState(
                    timestamp=now,
                    water_level=self.plant.water_level,
                    pressure=self.plant.pressure,
                    flow_rate=self.plant.flow_rate,
                    pump_status=self.plant.pump_status,
                    inlet_valve_status=self.plant.inlet_valve_status,
                    outlet_valve_status=self.plant.outlet_valve_status
                )
                session.add(plant_db)

                # PLCState
                plc_db = PLCState(
                    timestamp=now,
                    pump_status=self.plc.pump_status,
                    inlet_valve_status=self.plc.inlet_valve_status,
                    outlet_valve_status=self.plc.outlet_valve_status,
                    emergency_stopped=self.plc.emergency_stopped,
                    safety_trip=self.plc.safety_trip
                )
                session.add(plc_db)

                # CommunicationState
                comm_state = self.comms.get_state()
                comm_db = CommunicationState(
                    timestamp=now,
                    active_route=comm_state["active_route"],
                    session_id=comm_state["session_id"],
                    exposed_services=",".join(comm_state["exposed_services"]),
                    session_rotated=comm_state["session_rotated"]
                )
                session.add(comm_db)

                # SecurityState
                sec_state = self.security.get_state()
                sec_db = SecurityState(
                    timestamp=now,
                    level=sec_state["level"],
                    monitoring_frequency=sec_state["monitoring_frequency"],
                    attack_surface_restricted=sec_state["attack_surface_restricted"],
                    auth_required=sec_state["auth_required"],
                    mfa_enabled=sec_state["mfa_enabled"]
                )
                session.add(sec_db)

                # RiskState
                risk_state = self.risk.get_state()
                risk_db = RiskState(
                    timestamp=now,
                    risk_score=risk_state["risk_score"],
                    risk_level=risk_state["risk_level"],
                    reason=",".join(risk_state["recent_triggers"]) if risk_state["recent_triggers"] else "Normal Operation"
                )
                session.add(risk_db)

                # RecoveryState
                rec_state = self.recovery.get_state()
                rec_db = RecoveryState(
                    timestamp=now,
                    in_progress=rec_state["in_progress"],
                    stage=rec_state["stage"],
                    percentage=rec_state["percentage"],
                    est_seconds_remaining=rec_state["est_seconds_remaining"],
                    system_health=rec_state["system_health"]
                )
                session.add(rec_db)

                # AIAlert
                exp = getattr(self, "latest_ai_explanation", {})
                if exp:
                    ai_db = AIAlert(
                        timestamp=now,
                        decision=exp.get("decision", "MONITORING"),
                        threat_stage=exp.get("threat_stage", "Normal"),
                        risk_score=exp.get("risk_score", 0.0),
                        risk_level=exp.get("risk_level", "Low"),
                        confidence=exp.get("confidence", 100.0),
                        explanation_text=exp.get("raw_text", ""),
                        shap_attributions=exp.get("shap_attributions", {}),
                        shap_chart_base64=exp.get("shap_chart_base64", ""),
                        incident_playbook=exp.get("incident_playbook", {})
                    )
                    session.add(ai_db)

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error persisting state to database: {e}")

# Global singleton simulator instance
simulator_service = SimulatorService()
