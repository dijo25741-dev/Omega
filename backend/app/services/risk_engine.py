import logging
from typing import List, Dict

logger = logging.getLogger("omega.risk")

class RiskEngine:
    """
    Evaluates system threat telemetry and calculates a dynamic risk score (0-100).
    Automatically categorizes threats and triggers adaptive responses.
    """
    def __init__(self):
        self.risk_score = 5.0  # Default noise baseline
        self.risk_level = "LOW"
        self.recent_triggers: List[Dict[str, float]] = []
        self.decay_counter = 0

    def add_risk_event(self, event_name: str, points: float) -> float:
        """
        Increases the risk score by a given amount and tracks the trigger.
        Capped at 100.0.
        """
        self.risk_score = min(100.0, self.risk_score + points)
        self.recent_triggers.append({"event": event_name, "points": points})
        # Keep only the last 5 triggers for display
        if len(self.recent_triggers) > 5:
            self.recent_triggers.pop(0)
        
        self.recalculate_level()
        logger.info(f"Risk event registered: {event_name} (+{points} pts). Current Score: {round(self.risk_score, 1)}")
        return self.risk_score

    def decay_risk(self):
        """
        Decreasing risk over time when system operates normally.
        Decreases risk score by 1.0 point every 3 seconds, down to baseline of 5.0.
        """
        self.decay_counter += 1
        if self.decay_counter >= 3:
            self.decay_counter = 0
            if self.risk_score > 5.0:
                self.risk_score = max(5.0, self.risk_score - 1.0)
                self.recalculate_level()

    def recalculate_level(self):
        """Maps numerical risk score to categorical levels."""
        if self.risk_score <= 25.0:
            self.risk_level = "LOW"
        elif self.risk_score <= 50.0:
            self.risk_level = "MEDIUM"
        elif self.risk_score <= 75.0:
            self.risk_level = "HIGH"
        else:
            self.risk_level = "CRITICAL"

    def evaluate_telemetry(self, telemetry: dict, plc_status: dict) -> List[dict]:
        """
        Scans current physical plant metrics and PLC registers for anomalies.
        Returns a list of triggered risk events.
        """
        events = []
        
        # Scenario: Pump running dry / Inlet valve closed
        if telemetry["pump_status"] == "ON" and telemetry["inlet_valve_status"] == "CLOSED":
            events.append({
                "event": "Hazardous pump operation (Inlet Valve closed while Pump ON)",
                "points": 5.0
            })
            
        # Scenario: Overpressure
        if telemetry["pressure"] >= 5.5:
            events.append({
                "event": "High pressure sensor anomaly (>= 5.5 bar)",
                "points": 7.0
            })
            
        # Scenario: Near Overflow
        if telemetry["water_level"] >= 950.0:
            events.append({
                "event": "Tank level High-High limit alert (>= 950L)",
                "points": 3.0
            })
            
        # Scenario: Near Empty
        if telemetry["water_level"] <= 50.0 and telemetry["outlet_valve_status"] == "OPEN":
            events.append({
                "event": "Tank level Low-Low limit alert (<= 50L)",
                "points": 2.0
            })

        # Process detected events
        for e in events:
            self.add_risk_event(e["event"], e["points"])

        return events

    def get_state(self) -> dict:
        """Returns current risk summary."""
        return {
            "risk_score": round(self.risk_score, 1),
            "risk_level": self.risk_level,
            "recent_triggers": [t["event"] for t in self.recent_triggers]
        }

    def reset(self):
        """Resets risk metrics to default baseline."""
        self.risk_score = 5.0
        self.risk_level = "LOW"
        self.recent_triggers = []
        self.decay_counter = 0
