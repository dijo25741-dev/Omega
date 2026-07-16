class SecurityEngine:
    """
    Manages active security levels and restrictions for the ICS.
    Dynamically adjusts security posture based on the calculated risk.
    """
    def __init__(self):
        self.level = "LOW"
        self.monitoring_frequency = "NORMAL"
        self.attack_surface_restricted = False
        self.auth_required = False
        self.mfa_enabled = False

    def adapt_to_risk(self, risk_level: str) -> dict:
        """
        Dynamically adjusts the security controls and returns a description of updates.
        """
        self.level = risk_level
        old_mfa = self.mfa_enabled
        old_surface = self.attack_surface_restricted

        if risk_level == "LOW":
            self.monitoring_frequency = "NORMAL"
            self.attack_surface_restricted = False
            self.auth_required = False
            self.mfa_enabled = False
            
        elif risk_level == "MEDIUM":
            self.monitoring_frequency = "HIGH"
            self.attack_surface_restricted = False
            self.auth_required = True
            self.mfa_enabled = False
            
        elif risk_level == "HIGH":
            self.monitoring_frequency = "HIGH"
            self.attack_surface_restricted = True
            self.auth_required = True
            self.mfa_enabled = True
            
        elif risk_level == "CRITICAL":
            self.monitoring_frequency = "CRITICAL"
            self.attack_surface_restricted = True
            self.auth_required = True
            self.mfa_enabled = True

        changes = []
        if old_mfa != self.mfa_enabled:
            changes.append(f"MFA requirement set to {self.mfa_enabled}")
        if old_surface != self.attack_surface_restricted:
            changes.append(f"Attack surface restriction set to {self.attack_surface_restricted}")

        return {
            "level": self.level,
            "monitoring_frequency": self.monitoring_frequency,
            "attack_surface_restricted": self.attack_surface_restricted,
            "auth_required": self.auth_required,
            "mfa_enabled": self.mfa_enabled,
            "changes": changes
        }

    def get_state(self) -> dict:
        """Returns the current active security posture details."""
        return {
            "level": self.level,
            "monitoring_frequency": self.monitoring_frequency,
            "attack_surface_restricted": self.attack_surface_restricted,
            "auth_required": self.auth_required,
            "mfa_enabled": self.mfa_enabled
        }
