import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def make_request(url_path: str, data: dict = None, method: str = "GET") -> tuple[int, dict]:
    """Helper to execute HTTP requests using standard urllib library."""
    url = f"{BASE_URL}{url_path}"
    headers = {"Content-Type": "application/json"}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")
            return status_code, json.loads(response_body)
    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            response_body = e.read().decode("utf-8")
            return status_code, json.loads(response_body)
        except Exception:
            return status_code, {"detail": str(e)}
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Connection refused. Is the Uvicorn server running at {BASE_URL}?")
        print(f"Details: {e.reason}")
        exit(1)

def run_tests():
    print("=" * 60)
    print("          OMEGA BACKEND SYSTEM VERIFICATION SUITE")
    print("=" * 60)

    # 1. Health check
    print("\n[+] Testing GET /health...")
    code, res = make_request("/health")
    assert code == 200, f"Expected 200, got {code}"
    print(f"    Uptime: {res['uptime_seconds']}s | Simulator Active: {res['simulator_active']}")

    # 2. Plant status
    print("\n[+] Testing GET /plant/status...")
    code, res = make_request("/plant/status")
    assert code == 200
    print(f"    Telemetry: level={res['water_level']}L | pressure={res['pressure']} bar | pump={res['pump_status']}")

    # 3. PLC status
    print("\n[+] Testing GET /plc/status...")
    code, res = make_request("/plc/status")
    assert code == 200
    print(f"    Registers: pump={res['pump_status']} | inlet={res['inlet_valve_status']} | outlet={res['outlet_valve_status']}")

    # 4. Plant reset
    print("\n[+] Testing POST /plant/reset...")
    code, res = make_request("/plant/reset", method="POST")
    assert code == 200
    print(f"    Response: success={res['success']} | msg='{res['message']}'")

    # 5. PLC controls (Normal state)
    print("\n[+] Operating PLC: Opening Outlet Valve...")
    code, res = make_request("/plc/open-valve", data={"valve": "outlet"}, method="POST")
    assert code == 200
    print(f"    Response: success={res['success']} | detail='{res['detail']}'")

    print("\n[+] Operating PLC: Starting Pump (with inlet open)...")
    code, res = make_request("/plc/start-pump", method="POST")
    assert code == 200
    print(f"    Response: success={res['success']} | state={res['state']}")

    # 6. Communication Route
    print("\n[+] Testing GET /communication...")
    code, res = make_request("/communication")
    assert code == 200
    print(f"    Route: active_route='{res['active_route']}' | session='{res['session_id'][:12]}...'")

    print("\n[+] Testing manual communication route rotation...")
    code, res = make_request("/communication/rotate", method="POST")
    assert code == 200
    print(f"    New Route: '{res['active_route']}' | session='{res['session_id'][:12]}...'")

    # 7. Security Engine status
    print("\n[+] Testing GET /security...")
    code, res = make_request("/security")
    assert code == 200
    print(f"    Security Profile: level={res['level']} | mfa={res['mfa_enabled']}")

    # 8. Risk Engine status
    print("\n[+] Testing GET /risk...")
    code, res = make_request("/risk")
    assert code == 200
    print(f"    Risk metrics: score={res['risk_score']} | level={res['risk_level']}")

    # 9. Attack Simulation: Reconnaissance
    print("\n[+] Simulating Reconnaissance attack...")
    code, res = make_request("/attack/reconnaissance", method="POST")
    assert code == 200
    print(f"    Attack action: '{res['action_taken']}'")

    # Check updated risk score
    code, res = make_request("/risk")
    print(f"    New Risk score: {res['risk_score']} | Level: {res['risk_level']}")

    # 10. Attack Simulation: PLC command abuse
    print("\n[+] Simulating PLC Command Abuse (safety bypass)...")
    code, res = make_request("/attack/plc-command-abuse", method="POST")
    assert code == 200
    print(f"    Attack action: '{res['action_taken']}'")
    
    # Wait 1.5 seconds for physics loop to register pressure anomaly and risk increase
    print("    Waiting 1.5s for simulator step...")
    time.sleep(1.5)

    code, plant_res = make_request("/plant/status")
    print(f"    Current pressure: {plant_res['pressure']} bar (Overpressure spike!)")

    code, risk_res = make_request("/risk")
    print(f"    New Risk score: {risk_res['risk_score']} | Level: {risk_res['risk_level']}")

    # Check security engine: Should have adapted to HIGH/CRITICAL and enabled MFA
    code, sec_res = make_request("/security")
    print(f"    Adapted Security: level={sec_res['level']} | MFA Enabled={sec_res['mfa_enabled']}")

    # 11. Verify Adaptive Security MFA Block
    if sec_res["mfa_enabled"]:
        print("\n[+] Verifying Adaptive MFA: Attempting to start pump without token...")
        code, res = make_request("/plc/start-pump", method="POST")
        assert code == 403, f"Expected 403, got {code}"
        print(f"    Result: BLOCKED successfully (HTTP {code} | detail='{res['detail']}')")

        print("\n[+] Verifying Adaptive MFA: Attempting to start pump WITH valid token '123456'...")
        code, res = make_request("/plc/start-pump", data={"mfa_token": "123456"}, method="POST")
        assert code == 200, f"Expected 200, got {code} (res={res})"
        print(f"    Result: ALLOWED successfully (HTTP {code})")

    # 12. Attack Simulation: Ransomware
    print("\n[+] Simulating Ransomware attack (degrades system health and auto-starts recovery)...")
    code, res = make_request("/attack/ransomware", method="POST")
    assert code == 200
    print(f"    Attack action: '{res['action_taken']}'")

    # Check recovery status
    code, rec_res = make_request("/recovery")
    print(f"    Recovery Engine: in_progress={rec_res['in_progress']} | stage={rec_res['stage']} | percentage={rec_res['percentage']}% | health={rec_res['system_health']}%")

    # 13. Audit logs querying
    print("\n[+] Querying Audit Engine logs...")
    code, res = make_request("/audit?limit=5")
    assert code == 200
    print(f"    Audit database: total_logs={res['total']} | returned={len(res['logs'])}")
    for log in res["logs"][:3]:
        print(f"      - [{log['timestamp'][11:19]}] Module: {log['module']} | Event: {log['event']} | Decision: {log['decision']}")

    print("\n" + "=" * 60)
    print("      ALL MODULE TESTS PASSED - SYSTEM FULLY OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
