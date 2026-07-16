import requests
import time
from jose import jwt

BASE_URL = "http://localhost:8000"
DEVICE_ID = "omega-001"
JWT_SECRET = "supersecretkey"
ALGORITHM = "HS256"

def get_auth_token():
    # Helper to generate a test JWT Token
    payload = {
        "sub": "mobile_app_user",
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def run_tests():
    print("--- Running Mobile App Mock Client Tests ---")
    
    # 1. Register Device
    print("\n1. Registering device...")
    reg_res = requests.post(f"{BASE_URL}/register-device", json={
        "deviceId": DEVICE_ID,
        "owner": "Ramsankar"
    })
    print("Response:", reg_res.json())

    # 2. Get status before laptop connection (should be offline)
    print("\n2. Checking status before laptop starts...")
    status_res = requests.get(f"{BASE_URL}/device-status/{DEVICE_ID}")
    print("Response:", status_res.json())

    # Wait for laptop to connect
    print("\n[Action Required] Please start 'test_client_laptop.py' now to establish connection.")
    print("We will wait 10 seconds before continuing the test...")
    time.sleep(10)

    # 3. Get status after laptop connection (should be online)
    print("\n3. Checking status after laptop starts...")
    status_res = requests.get(f"{BASE_URL}/device-status/{DEVICE_ID}")
    print("Response:", status_res.json())

    # 4. Send LOCK command
    print("\n4. Sending LOCK command with authorization token...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    cmd_res = requests.post(f"{BASE_URL}/send-command", json={
        "deviceId": DEVICE_ID,
        "command": "LOCK"
    }, headers=headers)
    print("Response:", cmd_res.json())

    # 5. Fetch Command History
    print("\n5. Fetching Command History...")
    history_res = requests.get(f"{BASE_URL}/command-history")
    print("Response:", history_res.json())

if __name__ == "__main__":
    run_tests()
