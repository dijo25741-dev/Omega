import logging
from app.config import settings

logger = logging.getLogger(__name__)

THREAT_WEIGHTS = {
    "Normal": 0.0,
    "Reconnaissance": 15.0,
    "Credential Theft": 30.0,
    "Privilege Escalation": 50.0,
    "Lateral Movement": 70.0,
    "PLC Targeting": 90.0,
    "Ransomware": 98.0
}

class CNIRiskEngine:
    @staticmethod
    def calculate_risk(
        threat_prediction: str,
        threat_confidence: float,
        anomaly_score: float,
        device_trust: float,
        operator_trust: float,
        cpu_usage: float,
        memory_usage: float,
        network_latency: float,
        historical_incidents: int = 0
    ) -> dict:
        """
        Calculates a CNI-wide dynamic risk score (0-100).
        """
        # 1. Threat model score
        threat_base = THREAT_WEIGHTS.get(threat_prediction, 0.0)
        threat_score = threat_base * (threat_confidence / 100.0)
        
        # 2. Anomaly score mapping (Z-score to 0-100 scale)
        # Z-score of 3.0 maps to 50, Z-score of 6.0+ maps to 100
        anom_score_mapped = min(100.0, (anomaly_score / 6.0) * 100.0) if anomaly_score > 0 else 0.0
        
        # 3. Host / Entity penalties
        device_penalty = 100.0 - device_trust
        operator_penalty = 100.0 - operator_trust
        
        # 4. Device health (high CPU/Memory spikes risk)
        health_penalty = 0.0
        if cpu_usage > 85.0:
            health_penalty += 20.0
        if memory_usage > 85.0:
            health_penalty += 20.0
        health_penalty = min(health_penalty, 40.0)
        
        # 5. Network latency spikes
        network_penalty = min(100.0, (network_latency / 50.0) * 100.0) if network_latency > 5.0 else 0.0
        
        # 6. Weighted compilation
        # Weights: Threat (40%), Anomaly (20%), Operator trust (15%), Device trust (10%), Health (10%), Network (5%)
        raw_score = (
            (threat_score * 0.40) +
            (anom_score_mapped * 0.20) +
            (operator_penalty * 0.15) +
            (device_penalty * 0.10) +
            (health_penalty * 0.10) +
            (network_penalty * 0.05)
        )
        
        # Incorporate historical incidents multiplier
        incident_bump = min(15.0, historical_incidents * 3.0)
        raw_score += incident_bump
        
        # Threat override logic (critical threat stages should never have low risk scores)
        if threat_prediction in ["PLC Targeting", "Ransomware"] and raw_score < 75.0:
            raw_score = max(75.0, raw_score)
            
        risk_score = min(100.0, max(0.0, raw_score))
        
        # Determine classification
        if risk_score <= settings.RISK_THRESHOLD_LOW:
            level = "Low"
            color = "#10B981"  # Emerald green
        elif risk_score <= settings.RISK_THRESHOLD_MEDIUM:
            level = "Medium"
            color = "#F59E0B"  # Amber yellow
        elif risk_score <= settings.RISK_THRESHOLD_HIGH:
            level = "High"
            color = "#F97316"  # Orange
        else:
            level = "Critical"
            color = "#EF4444"  # Red
            
        return {
            "risk_score": round(risk_score, 1),
            "risk_level": level,
            "color_code": color,
            "metrics": {
                "threat_score": round(threat_score, 1),
                "anomaly_score": round(anom_score_mapped, 1),
                "operator_penalty": round(operator_penalty, 1),
                "device_penalty": round(device_penalty, 1),
                "health_penalty": round(health_penalty, 1),
                "network_penalty": round(network_penalty, 1),
                "historical_incidents_bump": round(incident_bump, 1)
            }
        }

# Singleton Instance
cni_risk_engine = CNIRiskEngine()
