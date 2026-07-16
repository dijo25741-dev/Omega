import pandas as pd
import numpy as np
import pickle
import os
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from app.config import settings

logger = logging.getLogger(__name__)

# Feature definition
FEATURES = [
    "network_latency",
    "failed_logins",
    "packet_rate",
    "cpu_usage",
    "memory_usage",
    "temp_deviation",
    "press_deviation",
    "flow_deviation",
    "volt_deviation",
    "curr_deviation",
    "anomalous_sequence_flag"
]

LABEL_MAP = {
    0: "Normal",
    1: "Reconnaissance",
    2: "Credential Theft",
    3: "Privilege Escalation",
    4: "Lateral Movement",
    5: "PLC Targeting",
    6: "Ransomware",
    7: "Command Injection",
    8: "Insider Threat"
}

REVERSE_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}

def generate_synthetic_data(num_samples: int = 2000) -> pd.DataFrame:
    """
    Generates high-fidelity synthetic CNI dataset mirroring different attack stages.
    """
    np.random.seed(42)
    
    samples_per_class = num_samples // len(LABEL_MAP)
    data = []
    
    for label_code, label_name in LABEL_MAP.items():
        for _ in range(samples_per_class):
            row = {}
            row["label"] = label_code
            
            # Default distributions per stage
            if label_name == "Normal":
                row["network_latency"] = np.random.normal(2.5, 0.8)
                row["failed_logins"] = int(np.random.choice([0, 1], p=[0.95, 0.05]))
                row["packet_rate"] = np.random.normal(80.0, 15.0)
                row["cpu_usage"] = np.random.uniform(5.0, 75.0)
                row["memory_usage"] = np.random.uniform(10.0, 85.0)
                row["temp_deviation"] = np.random.normal(0.0, 0.5)
                row["press_deviation"] = np.random.normal(0.0, 0.4)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 0.0
                
            elif label_name == "Reconnaissance":
                row["network_latency"] = np.random.normal(4.0, 1.2)
                row["failed_logins"] = int(np.random.choice([0, 1, 2], p=[0.70, 0.20, 0.10]))
                row["packet_rate"] = np.random.normal(250.0, 50.0)  # Port scans
                row["cpu_usage"] = np.random.uniform(5.0, 75.0)
                row["memory_usage"] = np.random.uniform(10.0, 85.0)
                row["temp_deviation"] = np.random.normal(0.0, 0.5)
                row["press_deviation"] = np.random.normal(0.0, 0.4)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 0.0
                
            elif label_name == "Credential Theft":
                row["network_latency"] = np.random.normal(5.0, 1.5)
                row["failed_logins"] = int(np.random.randint(3, 12))  # Brute forcing logins
                row["packet_rate"] = np.random.normal(180.0, 40.0)
                row["cpu_usage"] = np.random.uniform(5.0, 75.0)
                row["memory_usage"] = np.random.uniform(10.0, 85.0)
                row["temp_deviation"] = np.random.normal(0.0, 0.5)
                row["press_deviation"] = np.random.normal(0.0, 0.4)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 0.0
                
            elif label_name == "Privilege Escalation":
                row["network_latency"] = np.random.normal(3.5, 1.0)
                row["failed_logins"] = int(np.random.choice([0, 1], p=[0.90, 0.10]))
                row["packet_rate"] = np.random.normal(120.0, 25.0)
                row["cpu_usage"] = np.random.uniform(45.0, 75.0)  # Exploit payload execution
                row["memory_usage"] = np.random.uniform(40.0, 70.0)
                row["temp_deviation"] = np.random.normal(0.1, 0.6)
                row["press_deviation"] = np.random.normal(0.1, 0.5)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 0.0
                
            elif label_name == "Lateral Movement":
                row["network_latency"] = np.random.normal(8.0, 2.5)  # Network hopping latency
                row["failed_logins"] = int(np.random.choice([1, 2, 3], p=[0.60, 0.30, 0.10]))
                row["packet_rate"] = np.random.normal(400.0, 100.0)  # High traffic spikes
                row["cpu_usage"] = np.random.uniform(30.0, 60.0)
                row["memory_usage"] = np.random.uniform(35.0, 65.0)
                row["temp_deviation"] = np.random.normal(0.0, 0.5)
                row["press_deviation"] = np.random.normal(0.0, 0.4)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 0.0
                
            elif label_name == "PLC Targeting":
                row["network_latency"] = np.random.normal(4.5, 1.5)
                row["failed_logins"] = 0
                row["packet_rate"] = np.random.normal(150.0, 30.0)
                row["cpu_usage"] = np.random.uniform(25.0, 50.0)
                row["memory_usage"] = np.random.uniform(30.0, 60.0)
                # Significant industrial deviations caused by malicious PLC injection
                row["temp_deviation"] = np.random.choice([np.random.uniform(3.0, 10.0), np.random.uniform(-10.0, -3.0)])
                row["press_deviation"] = np.random.choice([np.random.uniform(2.5, 8.0), np.random.uniform(-8.0, -2.5)])
                row["flow_deviation"] = np.random.choice([np.random.uniform(2.0, 6.0), np.random.uniform(-6.0, -2.0)])
                row["volt_deviation"] = np.random.normal(1.5, 0.8)
                row["curr_deviation"] = np.random.normal(1.5, 0.8)
                row["anomalous_sequence_flag"] = 1.0  # Invalid order sequences sent to controller
                
            elif label_name == "Ransomware":
                row["network_latency"] = np.random.normal(15.0, 5.0)  # Substantial delay due to encrypted interfaces
                row["failed_logins"] = 0
                row["packet_rate"] = np.random.normal(600.0, 150.0)  # Intensive file copying/network activity
                row["cpu_usage"] = np.random.uniform(75.0, 99.0)  # Encryption utilizes high CPU
                row["memory_usage"] = np.random.uniform(70.0, 98.0)
                row["temp_deviation"] = np.random.normal(0.5, 1.0)
                row["press_deviation"] = np.random.normal(0.5, 1.0)
                row["flow_deviation"] = np.random.normal(0.0, 0.5)
                row["volt_deviation"] = np.random.normal(0.0, 0.5)
                row["curr_deviation"] = np.random.normal(0.0, 0.5)
                row["anomalous_sequence_flag"] = np.random.choice([0.0, 1.0], p=[0.70, 0.30])
                
            elif label_name == "Command Injection":
                row["network_latency"] = np.random.normal(6.5, 1.8)
                row["failed_logins"] = 0
                row["packet_rate"] = np.random.normal(300.0, 60.0)
                row["cpu_usage"] = np.random.uniform(50.0, 85.0)
                row["memory_usage"] = np.random.uniform(45.0, 75.0)
                row["temp_deviation"] = np.random.normal(0.0, 0.5)
                row["press_deviation"] = np.random.normal(0.0, 0.4)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 1.0
                
            elif label_name == "Insider Threat":
                row["network_latency"] = np.random.normal(2.5, 0.8)
                row["failed_logins"] = 0
                row["packet_rate"] = np.random.normal(80.0, 15.0)
                row["cpu_usage"] = np.random.uniform(10.0, 60.0)
                row["memory_usage"] = np.random.uniform(15.0, 70.0)
                row["temp_deviation"] = np.random.normal(0.0, 0.5)
                row["press_deviation"] = np.random.normal(0.0, 0.4)
                row["flow_deviation"] = np.random.normal(0.0, 0.3)
                row["volt_deviation"] = np.random.normal(0.0, 0.2)
                row["curr_deviation"] = np.random.normal(0.0, 0.2)
                row["anomalous_sequence_flag"] = 1.0
                
            data.append(row)
            
    df = pd.DataFrame(data)
    # Ensure numerical bounds
    for col in ["cpu_usage", "memory_usage"]:
        df[col] = df[col].clip(0.0, 100.0)
    df["network_latency"] = df["network_latency"].clip(0.1, 100.0)
    df["packet_rate"] = df["packet_rate"].clip(1.0, 2000.0)
    return df

def train_and_save_model(df: pd.DataFrame = None) -> RandomForestClassifier:
    if df is None:
        logger.info("Generating synthetic training dataset...")
        df = generate_synthetic_data()
        
    X = df[FEATURES]
    y = df["label"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate model
    accuracy = clf.score(X_test, y_test)
    logger.info(f"Model trained with validation accuracy: {accuracy:.4f}")
    
    # Save model
    with open(settings.MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    logger.info(f"Model saved to {settings.MODEL_PATH}")
    
    return clf

def load_threat_model() -> RandomForestClassifier:
    if not os.path.exists(settings.MODEL_PATH):
        logger.warning("Threat model file not found. Commencing training now...")
        return train_and_save_model()
        
    try:
        with open(settings.MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}. Retraining...")
        return train_and_save_model()
