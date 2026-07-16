import uuid
from typing import List

class CommunicationOrchestrator:
    """
    Simulates adaptive communication and routing security.
    Provides network obfuscation and session rotation.
    """
    def __init__(self):
        self.routes = ["Secure Route A", "Secure Route B", "Secure Route C"]
        self.current_route_index = 0
        self.session_id = str(uuid.uuid4())
        self.exposed_services = ["telemetry", "plc_control", "audit_logs", "recovery_config"]
        self.session_rotated = False

    def rotate_route(self) -> dict:
        """Rotates the communication route and updates session token."""
        self.current_route_index = (self.current_route_index + 1) % len(self.routes)
        self.session_id = str(uuid.uuid4())
        self.session_rotated = True
        
        return {
            "active_route": self.get_active_route(),
            "session_id": self.session_id,
            "event": "Communication channel rotated, session refreshed"
        }

    def get_active_route(self) -> str:
        return self.routes[self.current_route_index]

    def adapt_to_risk(self, risk_level: str) -> bool:
        """
        Adapts communication features and shrinks the attack surface
        according to the risk level. Returns True if a rotation occurred.
        """
        rotated = False
        
        if risk_level == "LOW":
            self.exposed_services = ["telemetry", "plc_control", "audit_logs", "recovery_config"]
            self.session_rotated = False
            
        elif risk_level == "MEDIUM":
            self.exposed_services = ["telemetry", "plc_control", "audit_logs"]
            # Medium risk: check if session needs refreshing
            if not self.session_rotated:
                self.rotate_route()
                rotated = True
                
        elif risk_level == "HIGH":
            self.exposed_services = ["telemetry", "plc_control"]
            # High risk: force rotate immediately
            self.rotate_route()
            rotated = True
            
        elif risk_level == "CRITICAL":
            # Isolate down to telemetry-only read access. Lock configuration endpoints.
            self.exposed_services = ["telemetry"]
            self.rotate_route()
            rotated = True

        return rotated

    def get_state(self) -> dict:
        """Returns current configuration parameters."""
        return {
            "active_route": self.get_active_route(),
            "session_id": self.session_id,
            "exposed_services": self.exposed_services,
            "session_rotated": self.session_rotated
        }
