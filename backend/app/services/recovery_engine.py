import logging
from typing import Tuple

logger = logging.getLogger("omega.recovery")

class RecoveryEngine:
    """
    Automates the containment and recovery sequence.
    Updates system health and moves through stages:
    CONTAIN -> RECOVER -> VERIFY -> RESUME -> NONE (Done)
    """
    def __init__(self):
        self.in_progress = False
        self.stage = "NONE"
        self.percentage = 0.0
        self.est_seconds_remaining = 0.0
        self.system_health = 100.0

    def start_recovery(self) -> Tuple[bool, str]:
        """Triggers the automated self-healing process."""
        if self.in_progress:
            return False, "Recovery already in progress"

        self.in_progress = True
        self.stage = "CONTAIN"
        self.percentage = 0.0
        self.est_seconds_remaining = 12.0  # 3 seconds per stage, 4 stages
        self.system_health = 30.0  # Degraded state
        
        logger.info("Omega Automated Recovery Engine initiated.")
        return True, "Recovery sequence started successfully"

    def step(self, plant, plc, comms, security, risk) -> Tuple[bool, str]:
        """
        Advances the recovery sequence by 1 second.
        Applies system actions depending on the current stage.
        """
        if not self.in_progress:
            return False, ""

        # Increment percentage
        step_increment = 100.0 / 12.0  # 12-second total duration
        self.percentage = min(100.0, self.percentage + step_increment)
        self.est_seconds_remaining = max(0.0, self.est_seconds_remaining - 1.0)
        
        # Increase system health gradually
        self.system_health = min(100.0, 30.0 + (self.percentage * 0.7))

        event_msg = ""

        # Stage Transition Management
        if self.percentage < 25.0:
            if self.stage != "CONTAIN":
                self.stage = "CONTAIN"
                event_msg = "Recovery Stage: CONTAIN - Terminating threat channels"
            
            # Action: Lock down network, rotate route
            comms.rotate_route()
            security.adapt_to_risk("CRITICAL")

        elif self.percentage < 50.0:
            if self.stage != "RECOVER":
                self.stage = "RECOVER"
                event_msg = "Recovery Stage: RECOVER - Re-flashing PLC registers"
            
            # Action: Clear PLC attack overrides and reset controller latches
            plc.safety_override_active = False
            plc.emergency_stopped = False
            plc.safety_trip = False
            plc.high_pressure_counter = 0

        elif self.percentage < 75.0:
            if self.stage != "VERIFY":
                self.stage = "VERIFY"
                event_msg = "Recovery Stage: VERIFY - Testing system pressure and integrity"
            
            # Action: Calm down plant physics, shut pump, open inlet
            plant.pump_status = "OFF"
            plant.inlet_valve_status = "OPEN"
            plant.outlet_valve_status = "CLOSED"
            # Return tank to a safe midway level if it overflowed or went dry
            if plant.water_level >= 950.0 or plant.water_level <= 50.0:
                plant.water_level = 500.0

        elif self.percentage < 100.0:
            if self.stage != "RESUME":
                self.stage = "RESUME"
                event_msg = "Recovery Stage: RESUME - Re-establishing SCADA session links"
            
            # Action: Reset risk baseline, lower security level
            risk.reset()
            security.adapt_to_risk("LOW")
            comms.adapt_to_risk("LOW")

        else:
            # Recovery finished
            self.in_progress = False
            self.stage = "NONE"
            self.percentage = 0.0
            self.est_seconds_remaining = 0.0
            self.system_health = 100.0
            event_msg = "Recovery Stage: COMPLETE - SCADA Core fully operational"
            logger.info("Omega Recovery completed. System health restored to 100%.")

        return True, event_msg

    def get_state(self) -> dict:
        """Returns the current recovery snapshot."""
        return {
            "in_progress": self.in_progress,
            "stage": self.stage,
            "percentage": round(self.percentage, 1),
            "est_seconds_remaining": round(self.est_seconds_remaining, 1),
            "system_health": round(self.system_health, 1)
        }

    def reset(self):
        """Resets the recovery status to idle."""
        self.in_progress = False
        self.stage = "NONE"
        self.percentage = 0.0
        self.est_seconds_remaining = 0.0
        self.system_health = 100.0
