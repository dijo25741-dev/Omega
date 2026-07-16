import logging
from app.ai.infrastructure_learning import cni_behavior_learner
from app.config import settings

logger = logging.getLogger(__name__)

CRITICAL_COMMANDS = ["SHUTDOWN_PUMP", "CLOSE_VALVE", "STOP_MOTOR", "SET_VOLTAGE_HIGH", "DISABLE_SAFETY_LIMIT"]

class CNICommandGuardian:
    @staticmethod
    def evaluate_command(
        operator: str,
        command: str,
        device_id: str,
        current_telemetry: dict,
        predicted_threat_stage: str,
        maintenance_active: bool = None
    ) -> dict:
        """
        Validates operator commands against operational contexts, plant physical parameters,
        and threat stages.
        """
        # Determine maintenance override state
        if maintenance_active is None:
            maintenance_active = settings.MAINTENANCE_SCHEDULE.get(device_id, False)

        # Retrieve trust metrics
        op_trust = cni_behavior_learner.operator_trust[operator]
        dev_trust = cni_behavior_learner.device_trust[device_id]
        
        # Check command history
        has_issued_before = cni_behavior_learner.has_operator_issued_command(operator, command)
        
        # Check sequence validity
        is_seq_valid, seq_prob = cni_behavior_learner.is_sequence_valid(device_id, command)
        
        reasons = []
        confidence = 90.0  # Base confidence level
        
        # Rule 1: Cyber Threat Stage override
        # In case of active host compromise, restrict critical modifications
        if predicted_threat_stage in ["PLC Targeting", "Ransomware"]:
            if command in CRITICAL_COMMANDS:
                cni_behavior_learner.report_violation(operator, is_operator=True, severity=30.0)
                return {
                    "allowed": False,
                    "decision": "BLOCKED",
                    "confidence": 98.0,
                    "reason": f"System under high threat level ({predicted_threat_stage}). Critical command '{command}' restricted."
                }
            else:
                reasons.append("Caution: System under cyber attack alert.")
                confidence = 95.0

        # Rule 2: Physical Plant Safety boundaries
        temp = current_telemetry.get("temperature", 50.0)
        press = current_telemetry.get("pressure", 3.0)
        
        # Overheating protection
        if command == "SHUTDOWN_PUMP" and temp > 85.0:
            if not maintenance_active:
                cni_behavior_learner.report_violation(operator, is_operator=True, severity=20.0)
                return {
                    "allowed": False,
                    "decision": "BLOCKED",
                    "confidence": 97.0,
                    "reason": f"Physical safety limit violation: Cannot shutdown coolant pump. Core temperature is critically high ({temp:.1f}°C)."
                }
            else:
                reasons.append("Maintenance bypass active: Pump shutdown allowed despite high temp.")
                confidence = 80.0

        # Overpressure protection
        if command == "CLOSE_VALVE" and press > 5.5:
            if not maintenance_active:
                cni_behavior_learner.report_violation(operator, is_operator=True, severity=25.0)
                return {
                    "allowed": False,
                    "decision": "BLOCKED",
                    "confidence": 99.0,
                    "reason": f"Physical safety limit violation: Cannot close release valve. Line pressure is critically high ({press:.1f} bar)."
                }
            else:
                reasons.append("Maintenance bypass active: Valve closure allowed under manual override.")
                confidence = 85.0

        # Rule 3: Operator Trust check
        if op_trust < 50.0:
            if command in CRITICAL_COMMANDS and not maintenance_active:
                return {
                    "allowed": False,
                    "decision": "BLOCKED",
                    "confidence": 92.0,
                    "reason": f"Blocked command. Operator trust rating is insufficient ({op_trust:.1f}%)."
                }
            else:
                reasons.append(f"Warning: Command executed by operator with low trust score ({op_trust:.1f}%).")
                confidence = 85.0

        # Rule 4: Operational Sequence Verification
        if not is_seq_valid and command in CRITICAL_COMMANDS:
            if not maintenance_active:
                cni_behavior_learner.report_violation(operator, is_operator=True, severity=15.0)
                return {
                    "allowed": False,
                    "decision": "BLOCKED",
                    "confidence": 91.0,
                    "reason": f"Sequence anomaly detected: Command transition to '{command}' violates operational patterns."
                }
            else:
                reasons.append("Sequence anomaly allowed under scheduled maintenance.")
                confidence = 75.0

        # Rule 5: First-time command check (Warning profile)
        if not has_issued_before:
            reasons.append(f"Note: Operator '{operator}' has never issued command '{command}' to '{device_id}' before.")
            confidence = min(confidence, 88.0)

        # Compilation of validation
        reason_str = "; ".join(reasons) if reasons else "Command complies with all safe operational constraints."
        
        # Learn valid sequence
        cni_behavior_learner.learn_telemetry_frame({
            "device_id": device_id,
            "operator": operator,
            "command": command
        })

        return {
            "allowed": True,
            "decision": "ALLOWED",
            "confidence": round(confidence, 1),
            "reason": reason_str
        }

# Singleton Instance
cni_command_guardian = CNICommandGuardian()
