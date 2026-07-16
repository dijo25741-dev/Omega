from typing import Tuple

class PLCController:
    """
    Virtual Programmable Logic Controller (PLC) for the Water Treatment Plant.
    Manages direct control commands and safety interlocks.
    """
    def __init__(self):
        self.emergency_stopped = False
        self.safety_trip = False
        self.safety_override_active = False  # Set during cyber-attacks to bypass safety logic
        self.high_pressure_counter = 0
        
        # PLC Command registers
        self.pump_status = "OFF"
        self.inlet_valve_status = "OPEN"
        self.outlet_valve_status = "CLOSED"

    def process_command(self, command: str, plant_state: dict) -> Tuple[bool, str]:
        """
        Executes a control command on the PLC.
        Enforces safety rules and returns (success, detail_message).
        """
        # Safety rules check
        if self.emergency_stopped and command not in ["RESET_ESTOP", "READ_SENSORS"]:
            return False, "Command rejected: PLC is emergency stopped"

        if self.safety_trip and command in ["START_PUMP"] and not self.safety_override_active:
            return False, "Command rejected: PLC safety trip active. Reset required"

        if command == "START_PUMP":
            if self.inlet_valve_status == "CLOSED" and not self.safety_override_active:
                return False, "Command rejected: Cannot start pump while inlet valve is CLOSED (safety interlock)"
            self.pump_status = "ON"
            return True, "Pump started successfully"

        elif command == "STOP_PUMP":
            self.pump_status = "OFF"
            return True, "Pump stopped successfully"

        elif command == "OPEN_INLET":
            self.inlet_valve_status = "OPEN"
            return True, "Inlet valve opened successfully"

        elif command == "CLOSE_INLET":
            if self.pump_status == "ON" and not self.safety_override_active:
                return False, "Command rejected: Cannot close inlet valve while pump is running (overpressure risk)"
            self.inlet_valve_status = "CLOSED"
            return True, "Inlet valve closed successfully"

        elif command == "OPEN_OUTLET":
            self.outlet_valve_status = "OPEN"
            return True, "Outlet valve opened successfully"

        elif command == "CLOSE_OUTLET":
            self.outlet_valve_status = "CLOSED"
            return True, "Outlet valve closed successfully"

        elif command == "EMERGENCY_STOP":
            self.emergency_stopped = True
            self.pump_status = "OFF"
            self.inlet_valve_status = "CLOSED"
            return True, "Emergency stop activated"

        elif command == "RESET_ESTOP":
            self.emergency_stopped = False
            self.safety_trip = False
            self.high_pressure_counter = 0
            return True, "Emergency stop and safety trips reset"

        elif command == "READ_SENSORS":
            return True, "Sensor readings completed"

        return False, f"Unknown command: {command}"

    def run_safety_checks(self, plant_simulator) -> Tuple[bool, str]:
        """
        Runs virtual PLC firmware safety loop (runs every second in background).
        If safety_override_active is True, ignores all safety limits (cyber-attack simulation).
        """
        if self.safety_override_active:
            return False, ""

        # Overflow Protection (Level > 980.0 liters)
        if plant_simulator.water_level >= 980.0:
            actions_taken = []
            if plant_simulator.pump_status == "ON":
                plant_simulator.pump_status = "OFF"
                actions_taken.append("PUMP STOPPED")
            if plant_simulator.inlet_valve_status == "OPEN":
                plant_simulator.inlet_valve_status = "CLOSED"
                actions_taken.append("INLET VALVE CLOSED")
            
            if actions_taken:
                self.safety_trip = True
                return True, f"PLC auto-trip: High-High level threshold exceeded (>=980L). Actions: {', '.join(actions_taken)}"

        # Overpressure Protection (Pressure > 5.5 bar)
        if plant_simulator.pressure >= 5.5:
            self.high_pressure_counter += 1
            if self.high_pressure_counter >= 3:
                actions_taken = []
                if plant_simulator.pump_status == "ON":
                    plant_simulator.pump_status = "OFF"
                    actions_taken.append("PUMP STOPPED")
                
                self.safety_trip = True
                self.high_pressure_counter = 0
                return True, f"PLC safety trip: Overpressure threshold exceeded (>=5.5 bar for 3s). Actions: {', '.join(actions_taken)}"
        else:
            self.high_pressure_counter = max(0, self.high_pressure_counter - 1)

        return False, ""

    def get_state(self) -> dict:
        """Returns the current internal PLC control status."""
        return {
            "emergency_stopped": self.emergency_stopped,
            "safety_trip": self.safety_trip,
            "safety_override_active": self.safety_override_active
        }
