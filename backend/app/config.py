import json
from typing import List, Union, Dict
from pydantic import field_validator
from pydantic_settings import BaseSettings

import os
import sys

def get_default_model_path() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "app/models/threat_model.pkl")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "models", "threat_model.pkl")

def get_default_database_url() -> str:
    if getattr(sys, 'frozen', False):
        db_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.dirname(base_dir)
    db_path = os.path.join(db_dir, "omega.db").replace("\\", "/")
    return f"sqlite+aiosqlite:///{db_path}"

class Settings(BaseSettings):
    APP_NAME: str = "Omega Cyber Resilience Core"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = get_default_database_url()
    MODEL_PATH: str = get_default_model_path()
    
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    SECRET_KEY: str = "super-secret-omega-resilience-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AI Brain Configurations
    ANOMALY_ZSCORE_THRESHOLD: float = 3.0
    DISTRUST_DECAY_RATE: float = 0.95
    RISK_THRESHOLD_LOW: float = 25.0
    RISK_THRESHOLD_MEDIUM: float = 50.0
    RISK_THRESHOLD_HIGH: float = 75.0
    
    MAINTENANCE_SCHEDULE: Dict[str, bool] = {
        "PUMP_01": False,
        "VALVE_01": False,
        "MOTOR_01": False,
        "PLC_01": False,
        "SCADA_01": False,
    }

    CNI_NODES: List[Dict] = [
        {"id": "SCADA_01", "type": "SCADA", "label": "SCADA Control Center"},
        {"id": "FIREWALL_01", "type": "Firewall", "label": "Boundary Firewall"},
        {"id": "DB_01", "type": "Database", "label": "Historian Database"},
        {"id": "PLC_01", "type": "PLC", "label": "Main PLC Controller"},
        {"id": "PUMP_01", "type": "Pump", "label": "Coolant Pump A"},
        {"id": "VALVE_01", "type": "Valve", "label": "Pressure Release Valve A"},
        {"id": "MOTOR_01", "type": "Motor", "label": "Pump Motor A"},
        {"id": "SENSOR_01", "type": "Sensor", "label": "Temperature Sensor 01"},
        {"id": "SENSOR_02", "type": "Sensor", "label": "Pressure Sensor 02"},
    ]

    CNI_EDGES: List[List[str]] = [
        ["SCADA_01", "FIREWALL_01"],
        ["FIREWALL_01", "DB_01"],
        ["FIREWALL_01", "PLC_01"],
        ["PLC_01", "PUMP_01"],
        ["PLC_01", "VALVE_01"],
        ["PLC_01", "MOTOR_01"],
        ["PLC_01", "SENSOR_01"],
        ["PLC_01", "SENSOR_02"],
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v:
                return ["*"]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return [x.strip() for x in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
