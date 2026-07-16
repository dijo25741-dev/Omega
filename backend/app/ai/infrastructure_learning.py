import numpy as np
import logging
from collections import defaultdict
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class CNIBehaviorLearner:
    def __init__(self):
        # Maps device_id -> parameter -> shift ("DAY" or "NIGHT") -> {mean, std, count}
        self.device_profiles = defaultdict(lambda: defaultdict(lambda: {
            "DAY": {"mean": 0.0, "std": 1.0, "count": 0},
            "NIGHT": {"mean": 0.0, "std": 1.0, "count": 0}
        }))
        
        # Maps operator_id -> command_history (set of commands issued)
        self.operator_commands = defaultdict(set)
        
        # Maps device_id -> last_command
        self.last_commands = {}
        
        # Maps (prev_command, next_command) -> frequency count
        self.sequence_transitions = defaultdict(int)
        
        # Dynamic trust scores
        self.device_trust = defaultdict(lambda: 100.0)
        self.operator_trust = defaultdict(lambda: 100.0)
        
        # Set up initial normal baseline ranges to avoid cold start issues
        self._seed_default_baselines()

    def _get_active_shift(self, timestamp_str: str = None) -> str:
        if not timestamp_str:
            return "DAY"
        try:
            # Handle ISO timestamps safely
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if 6 <= dt.hour < 18:
                return "DAY"
            return "NIGHT"
        except Exception:
            return "DAY"

    def _seed_default_baselines(self):
        # Seed default profiles for PUMP_01, VALVE_01, MOTOR_01, SENSOR_01, SENSOR_02
        default_envelopes = {
            "PUMP_01": {
                "temperature": {"DAY": (60.0, 5.0), "NIGHT": (52.0, 4.0)},
                "pressure": {"DAY": (4.0, 0.4), "NIGHT": (3.2, 0.3)},
                "flow": {"DAY": (50.0, 3.0), "NIGHT": (42.0, 2.5)},
                "voltage": {"DAY": (220.0, 2.0), "NIGHT": (220.0, 2.0)},
                "current": {"DAY": (15.0, 0.5), "NIGHT": (12.0, 0.4)}
            },
            "VALVE_01": {
                "temperature": {"DAY": (45.0, 3.0), "NIGHT": (38.0, 2.5)},
                "pressure": {"DAY": (3.5, 0.3), "NIGHT": (2.8, 0.2)},
                "flow": {"DAY": (45.0, 4.0), "NIGHT": (35.0, 3.0)},
                "voltage": {"DAY": (24.0, 0.5), "NIGHT": (24.0, 0.5)},
                "current": {"DAY": (2.0, 0.1), "NIGHT": (1.6, 0.08)}
            },
            "MOTOR_01": {
                "temperature": {"DAY": (75.0, 8.0), "NIGHT": (65.0, 6.0)},
                "voltage": {"DAY": (480.0, 5.0), "NIGHT": (480.0, 5.0)},
                "current": {"DAY": (30.0, 1.5), "NIGHT": (24.0, 1.2)}
            },
            "SENSOR_01": {
                "temperature": {"DAY": (55.0, 2.0), "NIGHT": (48.0, 1.8)},
            },
            "SENSOR_02": {
                "pressure": {"DAY": (3.8, 0.2), "NIGHT": (3.1, 0.15)},
            }
        }
        for device_id, params in default_envelopes.items():
            for param, shifts in params.items():
                for shift, (mean, std) in shifts.items():
                    self.device_profiles[device_id][param][shift] = {
                        "mean": mean,
                        "std": std,
                        "count": 100  # Seed count to give standard weights
                    }

    def learn_telemetry_frame(self, data: dict):
        device_id = data.get("device_id")
        if not device_id:
            return

        shift = self._get_active_shift(data.get("timestamp"))

        # 1. Update parameter distributions (Welford's incremental variance algorithm)
        parameters = ["temperature", "pressure", "flow", "voltage", "current"]
        for param in parameters:
            val = data.get(param)
            if val is not None:
                profile = self.device_profiles[device_id][param][shift]
                count = profile["count"] + 1
                mean = profile["mean"]
                std = profile["std"]
                
                # Incremental updates
                delta = val - mean
                new_mean = mean + delta / count
                
                # Update variance/std
                variance = std ** 2
                delta2 = val - new_mean
                new_variance = ((count - 1) * variance + delta * delta2) / count if count > 1 else 1.0
                new_std = np.sqrt(max(new_variance, 0.001))
                
                profile["mean"] = new_mean
                profile["std"] = new_std
                profile["count"] = count

        # 2. Operator history learning
        operator = data.get("operator")
        command = data.get("command")
        if operator and command:
            self.operator_commands[operator].add(command)
            
            # Sequence transition learning
            last_cmd = self.last_commands.get(device_id)
            if last_cmd:
                self.sequence_transitions[(last_cmd, command)] += 1
            self.last_commands[device_id] = command

        # 3. Trust recovery decay over time
        self.device_trust[device_id] = min(100.0, self.device_trust[device_id] + (100.0 - self.device_trust[device_id]) * (1.0 - settings.DISTRUST_DECAY_RATE))
        if operator:
            self.operator_trust[operator] = min(100.0, self.operator_trust[operator] + (100.0 - self.operator_trust[operator]) * (1.0 - settings.DISTRUST_DECAY_RATE))

    def evaluate_telemetry_anomaly(self, data: dict) -> tuple[bool, float, dict]:
        """
        Calculates anomaly score (max Z-score) across the numeric fields.
        Returns: (is_anomaly, anomaly_score, deviation_details)
        """
        device_id = data.get("device_id")
        if not device_id:
            return False, 0.0, {}

        shift = self._get_active_shift(data.get("timestamp"))

        max_z = 0.0
        deviations = {}
        parameters = ["temperature", "pressure", "flow", "voltage", "current"]
        
        for param in parameters:
            val = data.get(param)
            if val is not None:
                profile = self.device_profiles[device_id][param][shift]
                if profile["count"] > 5:  # Require minimum samples for baseline comparisons
                    mean = profile["mean"]
                    std = profile["std"]
                    z = abs(val - mean) / std if std > 0 else 0.0
                    deviations[param] = round(z, 2)
                    if z > max_z:
                        max_z = z
                        
        is_anomaly = max_z > settings.ANOMALY_ZSCORE_THRESHOLD
        
        # Penalize trust on anomaly detection
        if is_anomaly:
            self.device_trust[device_id] = max(0.0, self.device_trust[device_id] - 5.0 * max_z)
            
        return is_anomaly, float(max_z), deviations

    def has_operator_issued_command(self, operator: str, command: str) -> bool:
        return command in self.operator_commands[operator]

    def is_sequence_valid(self, device_id: str, next_command: str) -> tuple[bool, float]:
        """
        Verifies if sequence is known.
        Returns: (is_valid, sequence_probability)
        """
        last_cmd = self.last_commands.get(device_id)
        if not last_cmd:
            return True, 1.0  # Safe default if no previous commands exist
            
        # Get total transitions out of last_cmd
        transitions = {k: v for k, v in self.sequence_transitions.items() if k[0] == last_cmd}
        total_count = sum(transitions.values())
        
        if total_count == 0:
            return True, 1.0  # Cold start condition
            
        specific_count = self.sequence_transitions.get((last_cmd, next_command), 0)
        prob = specific_count / total_count
        
        # If transition has never been seen, flag invalid
        return specific_count > 0, float(prob)

    def report_violation(self, entity_id: str, is_operator: bool = True, severity: float = 20.0):
        if is_operator:
            self.operator_trust[entity_id] = max(0.0, self.operator_trust[entity_id] - severity)
        else:
            self.device_trust[entity_id] = max(0.0, self.device_trust[entity_id] - severity)

# Singleton Instance
cni_behavior_learner = CNIBehaviorLearner()
