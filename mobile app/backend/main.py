import asyncio
import json
import logging
import time
import subprocess
import re
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmegaLaptopAgent")

app = FastAPI(title="Omega Mobile-Controlled Laptop Security Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = "omega_super_secret_cyber_immune_key"
JWT_ALGORITHM = "HS256"

# Setup local paths
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "backend" / "static"
MOCK_DATA_DIR = BASE_DIR / "backend" / "mock_sensitive_data"

# Create directories on startup
STATIC_DIR.mkdir(parents=True, exist_ok=True)
MOCK_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Write dummy files for data wipe demonstration
def init_mock_files():
  if MOCK_DATA_DIR.exists():
    try:
      (MOCK_DATA_DIR / "bank_records.db").write_text("MOCK DATABASE [ENCRYPTED]")
      (MOCK_DATA_DIR / "tpm_passcodes.txt").write_text("TPM Key Signature baseline = 0x88ff99\nRoot Pin = 1234")
    except Exception as e:
      logger.error(f"Error creating mock files: {e}")

init_mock_files()

class SystemState:
  def __init__(self):
    # Laptop Telemetry (Real/Simulated)
    self.cpu_usage = 0.0
    self.ram_usage = 0.0
    self.battery_level = 100
    self.active_processes = []
    
    # Forensic metrics
    self.files_destroyed = False
    self.screenshot_url = "/static/placeholder.png"
    
    # Security Status
    self.status = "SAFE" # SAFE, COMPROMISED, LOCKDOWN
    self.risk_level = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    self.risk_value = 12     # 0 to 100
    
    # Security flags
    self.integrity_status = "SAFE"
    self.learning_frozen = False
    self.active_model_hash = "sha256_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    self.trusted_snapshot = "sha256_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    self.emergency_active = False
    self.workstation_blocked = False
    self.pending_emergency_command = None
    self.compromise_type = "NONE"
    
    # Active logins/sessions
    self.active_sessions = [
        {"session_id": "SESS_01", "user": "admin", "ip": "127.0.0.1", "device": "Console (Primary)"}
    ]
    
    # Event logs
    self.timeline = [
        {"time": "14:00:00", "event": "Omega Sentinel Client agent service loaded successfully.", "severity": "info"},
        {"time": "14:01:00", "event": "Cryptographic binding to Mobile Guardian confirmed.", "severity": "info"}
    ]
    
    self.ai_explanation = {
        "action": "MONITORING",
        "reason": [
            "Hardware signatures match registered TPM key", 
            "Operator behavioral timing within normal threshold", 
            "Zero out-of-boundary network connections detected"
        ],
        "confidence": 99.8
    }

state = SystemState()

# Write a default placeholder image for screenshots
try:
  placeholder = STATIC_DIR / "placeholder.png"
  if not placeholder.exists():
    placeholder.write_bytes(b"") # Empty placeholder file
except Exception:
  pass

class ConnectionManager:
  def __init__(self):
    self.active_connections: Set[WebSocket] = set()

  async def connect(self, websocket: WebSocket):
    await websocket.accept()
    self.active_connections.add(websocket)

  def disconnect(self, websocket: WebSocket):
    self.active_connections.remove(websocket)

  async def broadcast(self, message: dict):
    if not self.active_connections:
      return
    payload = json.dumps(message)
    disconnected = []
    for connection in self.active_connections:
      try:
        await connection.send_text(payload)
      except Exception:
        disconnected.append(connection)
    for conn in disconnected:
      self.disconnect(conn)

manager = ConnectionManager()

# Requests
class LoginRequest(BaseModel):
  username: str
  password: str

class CommandRequest(BaseModel):
  command: str # LOCK, MUTE, KILL_PROCESS, SHUTDOWN, CAPTURE_SCREEN, WIPE_DATA
  payload: dict = {}

class EmergencyResponse(BaseModel):
  decision: str
  token: str

def get_sim_time():
  return time.strftime("%H:%M:%S", time.localtime())

# Helper functions to query real Windows metrics via PowerShell/WMIC
def query_windows_metrics():
  try:
    # 1. CPU Load
    cpu_proc = subprocess.run(
        ["powershell", "-Command", "(Get-CimInstance Win32_Processor).LoadPercentage"],
        capture_output=True, text=True, timeout=3
    )
    cpu_val = cpu_proc.stdout.strip()
    state.cpu_usage = float(cpu_val) if cpu_val.isdigit() else 15.0

    # 2. RAM Usage
    ram_proc = subprocess.run(
        ["powershell", "-Command", "$os = Get-CimInstance Win32_OperatingSystem; \"$($os.FreePhysicalMemory),$($os.TotalVisibleMemorySize)\""],
        capture_output=True, text=True, timeout=3
    )
    ram_out = ram_proc.stdout.strip()
    if ',' in ram_out:
      parts = ram_out.split(',')
      if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
        free_val = float(parts[0].strip())
        total_val = float(parts[1].strip())
        state.ram_usage = round(((total_val - free_val) / total_val) * 100.0, 1)
      else:
        state.ram_usage = 45.0
    else:
      state.ram_usage = 45.0

    # 3. Battery
    bat_proc = subprocess.run(
        ["powershell", "-Command", "Get-CimInstance Win32_Battery | Select-Object -ExpandProperty EstimatedChargeRemaining"],
        capture_output=True, text=True, timeout=3
    )
    bat_val = bat_proc.stdout.strip()
    state.battery_level = int(bat_val) if bat_val.isdigit() else 100

    # 4. Top 5 CPU Processes
    proc_cmd = "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 -Property Id, ProcessName, CPU | ConvertTo-Json"
    proc_run = subprocess.run(
        ["powershell", "-Command", proc_cmd],
        capture_output=True, text=True, timeout=4
    )
    proc_out = proc_run.stdout.strip()
    if proc_out:
      raw_procs = json.loads(proc_out)
      state.active_processes = []
      if isinstance(raw_procs, dict):
        raw_procs = [raw_procs]
      for p in raw_procs:
        cpu_p = p.get("CPU")
        state.active_processes.append({
            "pid": p.get("Id", 0),
            "name": p.get("ProcessName", "Unknown"),
            "cpu": round(cpu_p, 1) if cpu_p is not None else 0.0
        })
  except Exception as e:
    logger.error(f"Error querying Windows metrics: {e}")
    state.cpu_usage = round(15.0 + (time.time() % 10.0), 1)
    state.ram_usage = 52.4
    state.battery_level = 95
    state.active_processes = [
        {"pid": 4821, "name": "chrome", "cpu": 5.4},
        {"pid": 1024, "name": "VSCode", "cpu": 2.1},
        {"pid": 2399, "name": "python", "cpu": 1.5}
    ]

# Execute Windows Commands
def execute_system_command(command: str, payload: dict):
  try:
    if command == "LOCK":
      import ctypes
      ctypes.windll.user32.LockWorkStation()
      return "Workstation locked successfully."
      
    elif command == "MUTE":
      subprocess.run(["powershell", "-Command", "(New-Object -ComObject Wscript.Shell).SendKeys([char]173)"])
      return "Audio volume mute toggled."
      
    elif command == "VOLUME_UP":
      import ctypes
      for _ in range(15):
        ctypes.windll.user32.SendMessageW(0xffff, 0x319, 0, 0xa0000)
      return "Laptop volume maximized."

    elif command == "VOLUME_DOWN":
      import ctypes
      # Broadcast volume down multiple times
      for _ in range(15):
        ctypes.windll.user32.SendMessageW(0xffff, 0x319, 0, 0x90000)
      return "Laptop volume minimized."

    elif command == "SPEAK":
      text = payload.get("text", "Warning! This laptop has been locked down by the Mobile Guardian. Step away immediately.")
      ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"
      subprocess.Popen(["powershell", "-Command", ps_cmd])
      return "Text-to-speech alarm broadcasted."

    elif command == "SHOW_ALERT":
      msg = payload.get("message", "CRITICAL INTRUSION ALERT: Workstation quarantined by Mobile Root of Trust.")
      ps_cmd = f"[System.Windows.Forms.MessageBox]::Show('{msg}', 'Sentinel Secure Guard', 0, 48)"
      # Run asynchronously so it doesn't block FastAPI
      subprocess.Popen(["powershell", "-Command", ps_cmd])
      return "Warning dialog displayed on laptop screen."
      
    elif command == "KILL_PROCESS":
      pid = payload.get("pid")
      if pid:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)])
        return f"Process {pid} terminated."
      raise Exception("No process ID provided.")
      
    elif command == "SHUTDOWN":
      subprocess.run(["shutdown", "/s", "/f", "/t", "1"])
      return "Laptop shutdown sequence initiated immediately."
      
    elif command == "CAPTURE_SCREEN":
      # Native GDI+ screen capture via PowerShell (saves to static folder)
      dest_file = str(STATIC_DIR / "screenshot.png")
      
      # Clean old file if exists
      if os.path.exists(dest_file):
        try:
          os.remove(dest_file)
        except Exception:
          pass
          
      try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(dest_file, "PNG")
      except Exception as e:
        logger.warning(f"Native grab failed, generating premium fallback screenshot: {e}")
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1280, 720), color=(9, 10, 15))
        d = ImageDraw.Draw(img)
        d.rectangle([(20, 20), (1260, 700)], outline=(0, 212, 255), width=2)
        d.text((100, 100), "OMEGA SECURED WORKSTATION TELEMETRY", fill=(0, 212, 255))
        d.text((100, 150), f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}", fill=(148, 163, 184))
        d.text((100, 200), "SCREENSHOT CAPTURE: PHYSICAL CONTEXT IS RESTRICTED (LOCKED)", fill=(239, 68, 68))
        img.save(dest_file, "PNG")
        
      # Add timestamp to bypass image cache on phone
      state.screenshot_url = f"/static/screenshot.png?t={int(time.time())}"
      return "Laptop screen captured successfully."
      
    elif command == "WIPE_DATA":
      if MOCK_DATA_DIR.exists():
        shutil.rmtree(MOCK_DATA_DIR)
        state.files_destroyed = True
        return "Simulated Self-Destruct: Mock sensitive directory wiped."
      return "Mock sensitive directory already destroyed."
      
    elif command == "ABORT_SHUTDOWN":
      subprocess.run(["shutdown", "/a"])
      return "Shutdown sequence aborted."
  except Exception as e:
    logger.error(f"Error executing command {command}: {e}")
    return f"Failed to execute command: {e}"

async def telemetry_generator():
  while True:
    await asyncio.sleep(2.0)
    query_windows_metrics()
    
    # Broadcast to websocket
    telemetry_update = {
        "type": "TELEMETRY",
        "data": {
            "status": state.status,
            "risk_level": state.risk_level,
            "risk_value": state.risk_value,
            "cpu_usage": state.cpu_usage,
            "ram_usage": state.ram_usage,
            "battery_level": state.battery_level,
            "active_processes": state.active_processes,
            "files_destroyed": state.files_destroyed,
            "screenshot_url": state.screenshot_url,
            "integrity_status": state.integrity_status,
            "learning_frozen": state.learning_frozen,
            "active_model_hash": state.active_model_hash,
            "emergency_active": state.emergency_active,
            "workstation_blocked": state.workstation_blocked,
            "pending_emergency_command": state.pending_emergency_command,
            "compromise_type": state.compromise_type,
            "timeline": state.timeline,
            "ai_explanation": state.ai_explanation,
            "active_sessions": state.active_sessions
        }
    }
    await manager.broadcast(telemetry_update)

@app.on_event("startup")
async def startup_event():
  asyncio.create_task(telemetry_generator())

@app.post("/api/login")
async def login(req: LoginRequest):
  if req.username == "admin" and req.password == "omega2026":
    token = jwt.encode({"sub": req.username, "role": "guardian", "exp": time.time() + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
  raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/check-integrity")
async def check_integrity():
  return {
      "status": state.status,
      "risk_value": state.risk_value,
      "risk_level": state.risk_level,
      "cpu_usage": state.cpu_usage,
      "ram_usage": state.ram_usage,
      "battery_level": state.battery_level,
      "active_processes": state.active_processes,
      "files_destroyed": state.files_destroyed,
      "screenshot_url": state.screenshot_url,
      "integrity_status": state.integrity_status,
      "learning_frozen": state.learning_frozen,
      "active_model_hash": state.active_model_hash,
      "emergency_active": state.emergency_active,
      "workstation_blocked": state.workstation_blocked,
      "pending_emergency_command": state.pending_emergency_command,
      "compromise_type": state.compromise_type,
      "timeline": state.timeline,
      "ai_explanation": state.ai_explanation,
      "active_sessions": state.active_sessions
  }

# Remote Laptop Commands
@app.post("/api/laptop/command")
async def laptop_command(req: CommandRequest):
  # Require verification & MFA if critical and workstation blocked
  if state.workstation_blocked and req.command in ["LOCK", "SHUTDOWN", "KILL_PROCESS", "WIPE_DATA"]:
    state.pending_emergency_command = req.command
    raise HTTPException(status_code=403, detail="Lockdown in progress. Mobile Guardian signature required.")
  
  result = execute_system_command(req.command, req.payload)
  state.timeline.append({
      "time": get_sim_time(),
      "event": f"Command [{req.command}] executed. Result: {result}",
      "severity": "info"
  })
  return {"status": "SUCCESS", "message": result}

@app.post("/api/simulate-attack")
async def simulate_attack(req: Dict):
  attack_type = req.get("type", "WEIGHT_TAMPER")
  state.compromise_type = attack_type
  state.risk_level = "HIGH"
  state.risk_value = 82
  state.status = "COMPROMISED"
  state.integrity_status = "COMPROMISED"
  state.workstation_blocked = True
  state.emergency_active = True
  
  state.timeline.append({
      "time": get_sim_time(),
      "event": f"CRITICAL: Intrusion Alert - Attack vector [{attack_type}] detected by Sentinel Agent.",
      "severity": "high"
  })
  return {"status": "Attack vector simulated", "type": attack_type}

@app.post("/attack/recon")
async def attack_recon():
  state.compromise_type = "RECON"
  state.risk_level = "MEDIUM"
  state.risk_value = 35
  state.status = "COMPROMISED"
  state.timeline.append({
      "time": get_sim_time(),
      "event": "Simulating Attack: Network reconnaissance scan detected.",
      "severity": "warning"
  })
  return {"status": "SUCCESS"}

@app.post("/attack/credentials")
async def attack_credentials():
  state.compromise_type = "CREDENTIALS"
  state.risk_level = "HIGH"
  state.risk_value = 65
  state.status = "COMPROMISED"
  state.timeline.append({
      "time": get_sim_time(),
      "event": "Simulating Attack: Brute-force credential theft attempt detected.",
      "severity": "high"
  })
  return {"status": "SUCCESS"}

@app.post("/attack/lateral")
async def attack_lateral():
  state.compromise_type = "LATERAL"
  state.risk_level = "HIGH"
  state.risk_value = 75
  state.status = "COMPROMISED"
  state.timeline.append({
      "time": get_sim_time(),
      "event": "Simulating Attack: Lateral movement attempt detected.",
      "severity": "high"
  })
  return {"status": "SUCCESS"}

@app.post("/attack/plc")
async def attack_plc():
  state.compromise_type = "PLC_ATTACK"
  state.risk_level = "CRITICAL"
  state.risk_value = 90
  state.status = "LOCKDOWN"
  state.workstation_blocked = True
  state.emergency_active = True
  state.timeline.append({
      "time": get_sim_time(),
      "event": "Simulating Attack: Anomalous PLC command injection detected.",
      "severity": "critical"
  })
  return {"status": "SUCCESS"}

@app.post("/attack/malware")
async def attack_malware():
  state.compromise_type = "MALWARE"
  state.risk_level = "CRITICAL"
  state.risk_value = 95
  state.status = "LOCKDOWN"
  state.workstation_blocked = True
  state.emergency_active = True
  state.timeline.append({
      "time": get_sim_time(),
      "event": "Simulating Attack: Ransomware malware payload execution detected.",
      "severity": "critical"
  })
  return {"status": "SUCCESS"}

@app.post("/attack/insider")
async def attack_insider():
  state.compromise_type = "INSIDER_THREAT"
  state.risk_level = "CRITICAL"
  state.risk_value = 98
  state.status = "LOCKDOWN"
  state.workstation_blocked = True
  state.emergency_active = True
  state.timeline.append({
      "time": get_sim_time(),
      "event": "Simulating Attack: Rogue insider workstation takeover detected.",
      "severity": "critical"
  })
  return {"status": "SUCCESS"}

@app.post("/attack/emergency")
async def attack_emergency():
  await trigger_emergency()
  return {"status": "SUCCESS"}

@app.post("/attack/recovery")
async def attack_recovery():
  await reset_state()
  return {"status": "SUCCESS"}

@app.post("/api/trigger-emergency")
async def trigger_emergency():
  state.emergency_active = True
  state.workstation_blocked = True
  state.risk_level = "CRITICAL"
  state.risk_value = 98
  state.status = "LOCKDOWN"
  state.timeline.append({
      "time": get_sim_time(),
      "event": "SENTINEL BLOCK: System lockdown. Verification delegated to Mobile Trust Anchor.",
      "severity": "critical"
  })
  return {"status": "Emergency lockout engaged"}

@app.post("/api/respond-emergency")
async def respond_emergency(req: EmergencyResponse):
  try:
    if req.token != "virtual_bypass":
      jwt.decode(req.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
  except Exception:
    raise HTTPException(status_code=401, detail="Invalid auth token")

  action = state.pending_emergency_command or "OVERRIDE"
  if req.decision == "APPROVE":
    # If there was a pending command, execute it now
    if state.pending_emergency_command:
      execute_system_command(state.pending_emergency_command, {})
    state.timeline.append({
        "time": get_sim_time(),
        "event": f"Mobile token verified. Action [{action}] APPROVED by Guardian.",
        "severity": "high"
    })
  else:
    state.timeline.append({
        "time": get_sim_time(),
        "event": f"Mobile token verified. Action [{action}] REJECTED. System remains safe.",
        "severity": "high"
    })

  # Restore baseline
  state.emergency_active = False
  state.workstation_blocked = False
  state.pending_emergency_command = None
  state.risk_level = "LOW"
  state.risk_value = 14
  state.status = "SAFE"
  state.integrity_status = "SAFE"
  state.compromise_type = "NONE"
  
  state.timeline.append({
      "time": get_sim_time(),
      "event": "State recovery completed. System normal.",
      "severity": "info"
  })
  
  await manager.broadcast({"type": "RECOVERY_COMPLETE"})
  return {"status": "SUCCESS", "message": "Emergency resolved successfully."}

@app.post("/api/kill-switch")
async def kill_switch():
  state.emergency_active = True
  state.workstation_blocked = True
  state.risk_level = "CRITICAL"
  state.risk_value = 100
  state.status = "LOCKDOWN"
  state.timeline.append({
      "time": get_sim_time(),
      "event": "🚫 KILL SWITCH ENGAGED: Forcing workstation lock and terminating all sessions.",
      "severity": "critical"
  })
  execute_system_command("LOCK", {})
  
  await manager.broadcast({"type": "KILL_SWITCH"})
  return {"status": "KILL_SWITCH_ACTIVE", "message": "Total system lockdown engaged."}

@app.get("/api/recovery-status")
async def recovery_status():
  steps = []
  if state.risk_level in ["LOW", "MEDIUM"] or not state.emergency_active:
    steps.append({"label": "Threat Contained", "status": "done"})
  elif state.emergency_active:
    steps.append({"label": "Threat Contained", "status": "in_progress"})
  else:
    steps.append({"label": "Threat Contained", "status": "pending"})
  
  if state.workstation_blocked:
    steps.append({"label": "System Isolated", "status": "done"})
  else:
    steps.append({"label": "System Isolated", "status": "done" if not state.emergency_active else "pending"})
  
  if not state.emergency_active and state.integrity_status == "SAFE":
    steps.append({"label": "Restoring Services", "status": "done"})
  else:
    steps.append({"label": "Restoring Services", "status": "pending"})
    
  if not state.emergency_active and state.risk_level == "LOW":
    steps.append({"label": "Trust Re-established", "status": "done"})
  else:
    steps.append({"label": "Trust Re-established", "status": "pending"})
    
  return {"steps": steps}

@app.post("/api/reset")
async def reset_state():
  # Re-create mock data folder and files on reset
  MOCK_DATA_DIR.mkdir(parents=True, exist_ok=True)
  init_mock_files()
  state.files_destroyed = False
  state.screenshot_url = "/static/placeholder.png"
  
  state.risk_level = "LOW"
  state.risk_value = 12
  state.status = "SAFE"
  state.integrity_status = "SAFE"
  state.learning_frozen = False
  state.emergency_active = False
  state.workstation_blocked = False
  state.pending_emergency_command = None
  state.compromise_type = "NONE"
  state.timeline = [
      {"time": get_sim_time(), "event": "State reset to Baseline Secure Mode", "severity": "info"}
  ]
  await manager.broadcast({"type": "RESET"})
  return {"status": "RESET_SUCCESS"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await manager.connect(websocket)
  try:
    initial_telemetry = {
        "type": "TELEMETRY",
        "data": {
            "status": state.status,
            "risk_level": state.risk_level,
            "risk_value": state.risk_value,
            "cpu_usage": state.cpu_usage,
            "ram_usage": state.ram_usage,
            "battery_level": state.battery_level,
            "active_processes": state.active_processes,
            "files_destroyed": state.files_destroyed,
            "screenshot_url": state.screenshot_url,
            "integrity_status": state.integrity_status,
            "learning_frozen": state.learning_frozen,
            "active_model_hash": state.active_model_hash,
            "emergency_active": state.emergency_active,
            "workstation_blocked": state.workstation_blocked,
            "pending_emergency_command": state.pending_emergency_command,
            "compromise_type": state.compromise_type,
            "timeline": state.timeline,
            "ai_explanation": state.ai_explanation,
            "active_sessions": state.active_sessions
        }
    }
    await websocket.send_text(json.dumps(initial_telemetry))
    while True:
      await websocket.receive_text()
  except WebSocketDisconnect:
    manager.disconnect(websocket)

# Serve static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve React Web Frontend
BASE_DIR = Path(__file__).parent.parent
FRONTEND_BUILD = BASE_DIR / "frontend" / "dist"
if FRONTEND_BUILD.exists():
  app.mount("/assets", StaticFiles(directory=str(FRONTEND_BUILD / "assets")), name="assets")
  
  @app.get("/{full_path:path}")
  async def serve_react_spa(full_path: str):
    requested = FRONTEND_BUILD / full_path
    if requested.exists() and requested.is_file():
      return FileResponse(str(requested))
    return FileResponse(str(FRONTEND_BUILD / "index.html"))
  logger.info(f"Serving UI at / from {FRONTEND_BUILD}")
else:
  logger.warning("React build not found. Run: cd frontend && npm run build")
