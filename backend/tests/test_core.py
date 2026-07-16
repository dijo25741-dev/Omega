import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ai.infrastructure_learning import cni_behavior_learner
from app.ai.threat_prediction import cni_threat_predictor
from app.ai.risk_engine import cni_risk_engine
from app.ai.command_guardian import cni_command_guardian
from app.ai.explainable_ai import cni_explainable_ai

client = TestClient(app)

def test_behavior_learning():
    learner = cni_behavior_learner
    assert "PUMP_01" in learner.device_profiles
    
    # Test anomaly evaluation (Normal value)
    normal_frame = {
        "device_id": "PUMP_01",
        "temperature": 60.2,
        "pressure": 4.0,
        "flow": 50.1,
        "voltage": 220.0,
        "current": 15.0,
        "timestamp": "2026-07-14T10:15:30.000000"
    }
    is_anom, z_score, deviations = learner.evaluate_telemetry_anomaly(normal_frame)
    assert not is_anom
    assert z_score < 3.0
    
    # Test anomaly evaluation (Out of bounds outlier during DAY shift)
    anomaly_frame = {
        "device_id": "PUMP_01",
        "temperature": 120.0,
        "pressure": 4.0,
        "flow": 50.1,
        "voltage": 220.0,
        "current": 15.0,
        "timestamp": "2026-07-14T10:15:30.000000"
    }
    is_anom, z_score, deviations = learner.evaluate_telemetry_anomaly(anomaly_frame)
    assert is_anom
    assert z_score > 3.0
    assert deviations["temperature"] > 3.0

def test_threat_prediction():
    # Verify predictions on normal payload
    normal_payload = {
        "network_latency": 1.8,
        "failed_logins": 0,
        "packet_rate": 75.0,
        "cpu_usage": 12.0,
        "memory_usage": 25.0,
        "temp_deviation": 0.1,
        "press_deviation": 0.2,
        "flow_deviation": 0.0,
        "volt_deviation": 0.0,
        "curr_deviation": 0.0,
        "anomalous_sequence_flag": 0.0
    }
    
    pred = cni_threat_predictor.predict_threat_stage(normal_payload)
    assert "predicted_attack" in pred
    assert "confidence" in pred
    assert "probabilities" in pred
    assert "next_likely_action" in pred

def test_risk_engine():
    # Test Risk calculations
    low_risk = cni_risk_engine.calculate_risk(
        threat_prediction="Normal",
        threat_confidence=99.0,
        anomaly_score=0.4,
        device_trust=100.0,
        operator_trust=100.0,
        cpu_usage=15.0,
        memory_usage=25.0,
        network_latency=1.8
    )
    assert low_risk["risk_score"] < 25.0
    assert low_risk["risk_level"] == "Low"
    
    critical_risk = cni_risk_engine.calculate_risk(
        threat_prediction="Ransomware",
        threat_confidence=95.0,
        anomaly_score=5.5,
        device_trust=20.0,
        operator_trust=10.0,
        cpu_usage=90.0,
        memory_usage=85.0,
        network_latency=22.0
    )
    assert critical_risk["risk_score"] > 80.0
    assert critical_risk["risk_level"] == "Critical"

def test_command_guardian():
    # Test ALLOW logic on normal reading operations
    telemetry = {"temperature": 60.0, "pressure": 4.0}
    verdict_allow = cni_command_guardian.evaluate_command(
        operator="Operator_Admin",
        command="READ_STATUS",
        device_id="PUMP_01",
        current_telemetry=telemetry,
        predicted_threat_stage="Normal"
    )
    assert verdict_allow["allowed"]
    assert verdict_allow["decision"] == "ALLOWED"
    
    # Test BLOCK logic for overheating critical limits
    overheat_telemetry = {"temperature": 92.0, "pressure": 4.0}
    verdict_block = cni_command_guardian.evaluate_command(
        operator="Operator_Admin",
        command="SHUTDOWN_PUMP",
        device_id="PUMP_01",
        current_telemetry=overheat_telemetry,
        predicted_threat_stage="Normal"
    )
    assert not verdict_block["allowed"]
    assert verdict_block["decision"] == "BLOCKED"
    assert "temperature" in verdict_block["reason"].lower()

def test_api_routes():
    # 1. Test Root Health
    response = client.get("/health")
    assert response.status_code == 200
    assert "HEALTHY" in response.json()["status"]
    
    # 2. Test /api/ai/predict
    payload = {
        "device_id": "PUMP_01",
        "temperature": 61.2,
        "pressure": 3.9,
        "failed_logins": 0,
        "packet_rate": 80.0
    }
    response = client.post("/api/ai/predict", json=payload)
    assert response.status_code == 200
    assert "predicted_attack" in response.json()
    
    # 3. Test /api/ai/validate-command
    cmd_payload = {
        "operator": "Operator_Tech",
        "command": "READ_STATUS",
        "device_id": "PUMP_01"
    }
    response = client.post("/api/ai/validate-command", json=cmd_payload)
    assert response.status_code == 200
    assert "decision" in response.json()
    
    # 4. Test /api/ai/graph
    response = client.get("/api/ai/graph")
    assert response.status_code == 200
    assert "nodes" in response.json()
    assert "edges" in response.json()
    
    # 5. Test /api/ai/dashboard
    response = client.get("/api/ai/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "plant_metrics" in data
    assert "ai_brain" in data
    assert "device_graph" in data
    
    # 6. Test /api/ai/explanation
    response = client.get("/api/ai/explanation")
    assert response.status_code == 200
    assert "decision" in response.json()

def test_shift_aware_baselines():
    learner = cni_behavior_learner
    assert learner._get_active_shift("2026-07-14T10:15:30.000000") == "DAY"
    assert learner._get_active_shift("2026-07-14T22:45:00.000000") == "NIGHT"

def test_playbook_generation():
    from app.ai.playbook_engine import cni_playbook_engine
    playbook = cni_playbook_engine.get_playbook("PLC Targeting", "PUMP_01", 92.5)
    assert playbook["active"]
    assert playbook["severity"] == "CRITICAL"
    assert len(playbook["steps"]) > 0
    assert "PUMP_01" in playbook["target_device"]

def test_shap_values():
    telemetry = {
        "network_latency": 15.0,
        "failed_logins": 5,
        "packet_rate": 300.0,
        "cpu_usage": 85.0
    }
    shap_vals = cni_explainable_ai.calculate_shap_values(telemetry, "Ransomware")
    assert isinstance(shap_vals, dict)
    assert shap_vals["cpu_usage"] > 0

def test_background_monitor():
    from app.services.monitor import host_monitor
    telemetry = host_monitor.collect_telemetry()
    assert "host_cpu" in telemetry
    assert "host_memory" in telemetry
    assert "total_processes" in telemetry
    assert "total_connections" in telemetry
    assert "device_health" in telemetry
    assert telemetry["device_health"] >= 10.0

def test_emergency_mode_and_controller_transfer():
    from app.services.simulator import simulator_service
    # Force reset first
    response_reset = client.post("/api/reset")
    assert response_reset.status_code == 200
    assert not simulator_service.workstation_blocked
    
    # 1. Trigger emergency lock
    response_emerg = client.post("/attack/emergency")
    assert response_emerg.status_code == 200
    assert simulator_service.workstation_blocked
    assert simulator_service.emergency_active
    
    # 2. Assert console actions are blocked with 403
    action_payload = {
        "action_type": "TOGGLE_PUMP",
        "payload": {}
    }
    response_action = client.post("/api/action", json=action_payload)
    assert response_action.status_code == 403
    assert "lock" in response_action.json()["detail"].lower() or "blocked" in response_action.json()["detail"].lower()

def test_recovery_and_restoration():
    from app.services.simulator import simulator_service
    # 1. Trigger recovery
    response_rec = client.post("/attack/recovery")
    assert response_rec.status_code == 200
    assert simulator_service.recovery.in_progress
    
    # 2. Stop recovery by calling reset (subsidies attack)
    response_reset = client.post("/api/reset")
    assert response_reset.status_code == 200
    assert not simulator_service.workstation_blocked
    assert not simulator_service.emergency_active

def test_audit_logs():
    response = client.get("/api/ai/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "ai_brain" in data
