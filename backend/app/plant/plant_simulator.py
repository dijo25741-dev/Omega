import random

class WaterTreatmentPlantSimulator:
    """
    Physical simulation of a water treatment plant tank, pump, valves, and sensors.
    Applies physics rules at each 1-second step.
    """
    def __init__(self):
        # Default physical parameters
        self.max_level = 1000.0  # liters
        self.water_level = 450.0  # liters (initial)
        self.pump_status = "OFF"
        self.inlet_valve_status = "OPEN"
        self.outlet_valve_status = "CLOSED"
        self.pressure = 1.9  # bar
        self.flow_rate = 0.0  # L/s (outlet flow)

    def step(self) -> dict:
        """
        Updates the physical state of the water plant by 1 second.
        Returns the updated telemetry parameters.
        """
        # Noise factor to make sensors look realistic and lively
        noise = random.uniform(-0.2, 0.2)
        
        # Calculate water flows
        inlet_flow = 0.0
        if self.pump_status == "ON" and self.inlet_valve_status == "OPEN":
            inlet_flow = 15.0 + random.uniform(-0.3, 0.3)
            
        outlet_flow = 0.0
        if self.outlet_valve_status == "OPEN" and self.water_level > 0.0:
            # Outlet flow is limited by water available
            outlet_flow = min(10.0 + random.uniform(-0.2, 0.2), self.water_level)
            
        # Update water level
        self.water_level += (inlet_flow - outlet_flow)
        # Boundary constraints
        if self.water_level < 0.0:
            self.water_level = 0.0
        elif self.water_level > self.max_level:
            self.water_level = self.max_level
            
        # Update system pressure (measured at pump inlet manifold)
        static_pressure = 1.0 + (self.water_level / 500.0) # head pressure
        
        if self.pump_status == "ON":
            if self.inlet_valve_status == "OPEN":
                # Normal operation under pump pressure
                self.pressure = static_pressure + 1.5 + noise
            else:
                # Pump is ON but inlet valve is CLOSED: Pressure spike!
                self.pressure = 6.0 + random.uniform(-0.4, 0.4)
        else:
            # Pump is OFF, only static head pressure remains
            self.pressure = static_pressure + noise
            if self.pressure < 0.0:
                self.pressure = 0.0

        # Flow rate sensor reports outlet flow
        self.flow_rate = max(0.0, outlet_flow)

        return self.get_telemetry()

    def get_telemetry(self) -> dict:
        """Returns a snapshot of the current plant metrics."""
        return {
            "water_level": round(self.water_level, 2),
            "pressure": round(self.pressure, 2),
            "flow_rate": round(self.flow_rate, 2),
            "pump_status": self.pump_status,
            "inlet_valve_status": self.inlet_valve_status,
            "outlet_valve_status": self.outlet_valve_status,
        }

    def reset(self):
        """Resets the plant to normal safe initial values."""
        self.water_level = 450.0
        self.pump_status = "OFF"
        self.inlet_valve_status = "OPEN"
        self.outlet_valve_status = "CLOSED"
        self.pressure = 1.9
        self.flow_rate = 0.0
