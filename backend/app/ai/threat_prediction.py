import pandas as pd
import numpy as np
import logging
from app.models.ml_models import load_threat_model, train_and_save_model, FEATURES, LABEL_MAP, REVERSE_LABEL_MAP
from app.ai.infrastructure_learning import cni_behavior_learner

logger = logging.getLogger(__name__)

KILL_CHAIN_TRANSITIONS = {
    "Normal": "Reconnaissance (Network Scanning)",
    "Reconnaissance": "Credential Theft (Brute force logins)",
    "Credential Theft": "Privilege Escalation (Unauthorized admin access)",
    "Privilege Escalation": "Lateral Movement (Pivot to internal industrial subnets)",
    "Lateral Movement": "PLC Targeting (Altering firmware or operational metrics)",
    "PLC Targeting": "Ransomware (Locking HMI panels / encrypting workstations)",
    "Ransomware": "Critical Plant Failure / Shutdown",
    "Command Injection": "PLC Register Tampering / Process Hijack",
    "Insider Threat": "Unauthorized Command Sequence Engagement"
}

class CNIThreatPredictor:
    def __init__(self):
        self.model = load_threat_model()

    def predict_threat_stage(self, telemetry_frame: dict) -> dict:
        """
        Runs ML prediction based on live telemetry frame.
        """
        try:
            features_dict = self._extract_features(telemetry_frame)
            df = pd.DataFrame([features_dict])
            
            # Predict
            probs = self.model.predict_proba(df[FEATURES])[0]
            pred_idx = np.argmax(probs)
            
            predicted_stage = LABEL_MAP[pred_idx]
            confidence = float(probs[pred_idx])
            
            # Probability map
            prob_map = {LABEL_MAP[i]: float(probs[i]) for i in range(len(probs))}
            
            next_action = KILL_CHAIN_TRANSITIONS.get(predicted_stage, "Unknown")
            
            return {
                "predicted_attack": predicted_stage,
                "confidence": round(confidence * 100, 2),
                "probabilities": {k: round(v * 100, 2) for k, v in prob_map.items()},
                "next_likely_action": next_action
            }
        except Exception as e:
            logger.error(f"Error predicting threat stage: {e}")
            # Safe default fallback
            return {
                "predicted_attack": "Normal",
                "confidence": 100.0,
                "probabilities": {"Normal": 100.0},
                "next_likely_action": "Reconnaissance (Network Scanning)"
            }

    def retrain_model_from_db(self, records: list = None) -> bool:
        """
        Auto-retraining function. Updates threat model.
        """
        try:
            if not records:
                # If no DB records are provided, train on newly generated synthetic data
                from app.models.ml_models import generate_synthetic_data
                df = generate_synthetic_data(1500)
                logger.info("No DB records provided for retraining. Using synthetic data.")
                self.model = train_and_save_model(df)
                return True
                
            if len(records) < 10:
                logger.warning("Insufficient telemetry records in DB for retraining. Minimum of 10 required.")
                return False
                
            # Build training dataframe from database records
            data_rows = []
            for r in records:
                # Compute deviations based on current learner baseline
                _, _, devs = cni_behavior_learner.evaluate_telemetry_anomaly(r)
                
                label = 0
                if r.get("failed_logins", 0) > 3:
                    label = 2  # Credential Theft
                elif r.get("packet_rate", 0) > 350:
                    label = 4  # Lateral Movement
                elif r.get("cpu_usage", 0) > 80:
                    label = 6  # Ransomware
                elif r.get("is_anomaly") == 1:
                    label = 5  # PLC Targeting
                
                row = {
                    "network_latency": r.get("network_latency", 2.0),
                    "failed_logins": r.get("failed_logins", 0),
                    "packet_rate": r.get("packet_rate", 100.0),
                    "cpu_usage": r.get("cpu_usage", 15.0),
                    "memory_usage": r.get("memory_usage", 25.0),
                    "temp_deviation": devs.get("temperature", 0.0),
                    "press_deviation": devs.get("pressure", 0.0),
                    "flow_deviation": devs.get("flow", 0.0),
                    "volt_deviation": devs.get("voltage", 0.0),
                    "curr_deviation": devs.get("current", 0.0),
                    "anomalous_sequence_flag": 1.0 if (r.get("command") and "INVALID" in str(r.get("command"))) else 0.0,
                    "label": label
                }
                data_rows.append(row)
                
            df_db = pd.DataFrame(data_rows)
            # Mix with synthetic dataset to retain general patterns and class balance
            from app.models.ml_models import generate_synthetic_data
            df_synth = generate_synthetic_data(1000)
            
            df_combined = pd.concat([df_db, df_synth], ignore_index=True)
            
            logger.info("Executing model retraining...")
            self.model = train_and_save_model(df_combined)
            return True
        except Exception as e:
            logger.error(f"Error during auto-retraining: {e}")
            return False

    def _extract_features(self, frame: dict) -> dict:
        # Evaluate Z-score deviations from the running learner instance
        _, _, deviations = cni_behavior_learner.evaluate_telemetry_anomaly(frame)
        
        # Check command sequence validation
        anom_seq_flag = 0.0
        cmd = frame.get("command")
        dev_id = frame.get("device_id")
        if cmd and dev_id:
            is_seq_ok, _ = cni_behavior_learner.is_sequence_valid(dev_id, cmd)
            if not is_seq_ok:
                anom_seq_flag = 1.0

        return {
            "network_latency": float(frame.get("network_latency", 2.5)),
            "failed_logins": int(frame.get("failed_logins", 0)),
            "packet_rate": float(frame.get("packet_rate", 80.0)),
            "cpu_usage": float(frame.get("cpu_usage", 20.0)),
            "memory_usage": float(frame.get("memory_usage", 30.0)),
            "temp_deviation": float(deviations.get("temperature", 0.0)),
            "press_deviation": float(deviations.get("pressure", 0.0)),
            "flow_deviation": float(deviations.get("flow", 0.0)),
            "volt_deviation": float(deviations.get("voltage", 0.0)),
            "curr_deviation": float(deviations.get("current", 0.0)),
            "anomalous_sequence_flag": anom_seq_flag
        }

# Singleton Instance
cni_threat_predictor = CNIThreatPredictor()
