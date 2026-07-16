import asyncio
import json
import os
import time
import logging
import platform
import subprocess
import websockets
from pathlib import Path
from app.config import settings
from app.services.simulator import simulator_service
from app.websocket.manager import manager
from app.services.monitor import host_monitor
from app.security.command_verifier import verify_command_token, verify_command_signature

logger = logging.getLogger("omega.agent_client")

# Load config
CLOUD_WS_URL = os.environ.get("CLOUD_WS_URL", "ws://localhost:8000/ws/omega-001")
DEVICE_ID = "omega-001"

websocket_client = None

async def send_to_cloud(message):
    global websocket_client
    if websocket_client and websocket_client.state.name == "OPEN":
        try:
            if isinstance(message, str):
                await websocket_client.send(message)
            else:
                await websocket_client.send(json.dumps(message))
        except Exception as e:
            logger.error(f"[AGENT] Error sending to cloud: {e}")

# Override manager.broadcast so the simulator sends updates to the cloud!
async def agent_broadcast(message: dict):
    await send_to_cloud(message)

manager.broadcast = agent_broadcast

def verify_received_command(data: dict) -> bool:
    cmd = data.get("command")
    token = data.get("token")
    sig = data.get("signature")
    ts = data.get("timestamp")
    
    if not cmd or not token or not sig or not ts:
        logger.error(f"[AGENT] Rejected command: Missing verification fields. Data: {data}")
        return False
        
    # Verify JWT
    if not verify_command_token(token):
        logger.error("[AGENT] Rejected command: Invalid or expired JWT token.")
        return False
        
    # Verify HMAC signature
    if not verify_command_signature(cmd, ts, sig):
        logger.error("[AGENT] Rejected command: HMAC signature verification failed.")
        return False
        
    return True

async def execute_lock_system():
    logger.info("[AGENT] Executing LOCK_SYSTEM...")
    simulator_service.workstation_locked = True
    simulator_service.physical_locked = True
    
    now_str = datetime_str()
    simulator_service.timeline.append({
        "time": now_str,
        "event": "CYBER-IMMUNITY ENGAGED: Workstation lockout triggered locally.",
        "severity": "critical"
    })
    
    # Lock physical Windows workstation
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            logger.info("[AGENT] Workstation locked physically.")
        except Exception as e:
            logger.error(f"[AGENT] Failed to run LockWorkStation API: {e}")
    else:
        logger.info("[AGENT] Physical locking simulated (non-Windows OS).")

async def execute_shutdown():
    logger.info("[AGENT] Executing SHUTDOWN...")
    simulator_service.timeline.append({
        "time": datetime_str(),
        "event": "CRITICAL: System Shutdown command received.",
        "severity": "critical"
    })
    
    # Real Windows shutdown
    if platform.system() == "Windows":
        try:
            logger.warning("[AGENT] Triggering real Windows shutdown immediately...")
            subprocess.run("shutdown /s /f /t 1", shell=True)
        except Exception as e:
            logger.error(f"[AGENT] Failed to initiate Windows shutdown: {e}")
    else:
        logger.info("[AGENT] Shutdown simulated (non-Windows OS).")
        
    await simulator_service.stop()

async def execute_logout():
    logger.info("[AGENT] Executing LOGOUT...")
    # Simulate logging out virtual SCADA operator
    simulator_service.virtual_mobile_authorized = False
    simulator_service.timeline.append({
        "time": datetime_str(),
        "event": "SECURITY: Operator session terminated via Cloud command.",
        "severity": "warning"
    })
    logger.info("[AGENT] User Logout simulated (SCADA authorization revoked).")

async def execute_disable_network():
    logger.info("[AGENT] Executing DISABLE_NETWORK...")
    # Simulate network disruption by putting the communication route in a DISRUPTED state
    simulator_service.comms.routes = ["DISRUPTED"]
    simulator_service.comms.current_route_index = 0
    simulator_service.timeline.append({
        "time": datetime_str(),
        "event": "SECURITY: Network adapter interface disabled.",
        "severity": "warning"
    })
    logger.warning("[AGENT] Network Adapter disable simulated (virtual routes disrupted).")

async def execute_capture_screen():
    logger.info("[AGENT] Executing CAPTURE_SCREEN...")
    base_dir = Path(__file__).parent.parent
    static_dir = base_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    dest_file = str(static_dir / "screenshot.png")
    
    if os.path.exists(dest_file):
        try:
            os.remove(dest_file)
        except Exception:
            pass

    # If the physical workstation is locked, GDI capture will fail/access-denied. Use Pillow mockup directly.
    is_locked = getattr(simulator_service, "physical_locked", False)
    captured = False

    if not is_locked and platform.system() == "Windows":
        ps_script = f"""
        [Reflection.Assembly]::LoadWithPartialName("System.Drawing") | Out-Null
        [Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object System.Drawing.Bitmap([int]$bounds.Width, [int]$bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
        $graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bmp.Size)
        $bmp.Save("{dest_file}", [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $bmp.Dispose()
        """
        try:
            res = subprocess.run(["powershell", "-Command", ps_script], timeout=4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0 and os.path.exists(dest_file) and os.path.getsize(dest_file) > 0:
                captured = True
        except Exception as ps_err:
            logger.warning(f"[AGENT] Powershell capture failed: {ps_err}.")
        
    if not captured:
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1280, 800), color=(10, 15, 26))
            d = ImageDraw.Draw(img)
            # Outer cyber-immune boundary lines
            d.rectangle([(20, 20), (1260, 780)], outline=(0, 230, 255), width=3)
            d.rectangle([(30, 30), (1250, 770)], outline=(100, 100, 100), width=1)
            
            # Header
            d.text((80, 80), "=== OMEGA CYBER-IMMUNE CORE ===", fill=(0, 230, 255))
            d.text((80, 120), "SCADA CONTROL CONSOLE: LOCKED & ISOLATED", fill=(255, 60, 60))
            d.text((80, 160), "STATUS: WORKSTATION INTRUSION INTERCEPTED", fill=(255, 165, 0))
            
            # Dynamic telemetry details
            p_status = simulator_service.plc.pump_status
            v_status = simulator_service.plc.inlet_valve_status
            w_level = simulator_service.plant.water_level
            
            d.text((80, 220), f"PRIMARY PUMP STATUS  : {p_status}", fill=(255, 255, 255))
            d.text((80, 250), f"INLET VALVE STATUS   : {v_status}", fill=(255, 255, 255))
            d.text((80, 280), f"WATER TANK LEVEL     : {w_level:.2f} m", fill=(255, 255, 255))
            
            d.text((80, 350), "[SYSTEM ACTIONS DELEGATED TO MOBILE GUARDIAN APP]", fill=(0, 255, 0))
            d.text((80, 390), "Local mouse/keyboard inputs suspended to prevent override.", fill=(150, 150, 150))
            d.text((80, 420), "Awaiting secure Mobile token validation to restore console...", fill=(150, 150, 150))
            img.save(dest_file)
            logger.info("[AGENT] Pillow mock CNI screenshot generated successfully.")
        except Exception as pil_err:
            logger.error(f"[AGENT] Pillow fallback failed: {pil_err}")
            with open(dest_file, "wb") as f:
                f.write(b"MOCK SCREENSHOT")

    simulator_service.screenshot_url = f"/static/screenshot.png?t={int(time.time())}"
    logger.info(f"[AGENT] Screenshot url set: {simulator_service.screenshot_url}")

async def execute_mute():
    logger.info("[AGENT] Executing MUTE...")
    simulator_service.timeline.append({
        "time": datetime_str(),
        "event": "SECURITY: Workstation volume mute status toggled.",
        "severity": "warning"
    })
    if platform.system() == "Windows":
        try:
            # Send VK_VOLUME_MUTE (0xAD) via PowerShell
            subprocess.run(["powershell", "-Command", "$obj = new-object -com wscript.shell; $obj.SendKeys([char]173)"], shell=True)
            logger.info("[AGENT] System volume mute toggled via PowerShell.")
        except Exception as e:
            logger.error(f"[AGENT] Failed to toggle volume mute: {e}")

async def execute_wipe_data():
    logger.info("[AGENT] Executing WIPE_DATA...")
    simulator_service.files_destroyed = True
    simulator_service.timeline.append({
        "time": datetime_str(),
        "event": "SECURITY: Mock sensitive directories securely wiped.",
        "severity": "critical"
    })
    logger.info("[AGENT] Simulated Self-Destruct: Mock sensitive directory wiped.")

def datetime_str():
    return time.strftime("%H:%M:%S", time.localtime())

async def handle_agent_command(data: dict):
    if not verify_received_command(data):
        response = {
            "type": "COMMAND_RESPONSE",
            "status": "failure",
            "reason": "Authenticity check failed",
            "command": data.get("command", "UNKNOWN"),
            "timestamp": str(int(time.time()))
        }
        await send_to_cloud(response)
        return
        
    cmd = data.get("command")
    logger.info(f"[AGENT] Authenticated command received: {cmd}")
    
    status = "success"
    reason = ""
    
    try:
        if cmd in ["LOCK_SYSTEM", "LOCK"]:
            await execute_lock_system()
        elif cmd == "SHUTDOWN":
            await execute_shutdown()
        elif cmd == "LOGOUT":
            await execute_logout()
        elif cmd == "DISABLE_NETWORK":
            await execute_disable_network()
        elif cmd == "CAPTURE_SCREEN":
            await execute_capture_screen()
        elif cmd == "WIPE_DATA":
            await execute_wipe_data()
        elif cmd.startswith("MOUSE:"):
            parts = cmd.split(":")
            dx = float(parts[1])
            dy = float(parts[2])
            click = parts[3] if len(parts) > 3 else ""
            if platform.system() == "Windows":
                try:
                    import ctypes
                    class POINT(ctypes.Structure):
                        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                    pt = POINT()
                    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                    ctypes.windll.user32.SetCursorPos(pt.x + int(dx), pt.y + int(dy))
                    if click == "left":
                        ctypes.windll.user32.mouse_event(0x0002 | 0x0004, 0, 0, 0, 0)
                    elif click == "right":
                        ctypes.windll.user32.mouse_event(0x0008 | 0x0010, 0, 0, 0, 0)
                except Exception as e:
                    logger.error(f"[AGENT] Error performing mouse action: {e}")
            else:
                logger.info(f"[AGENT] Simulated Mouse Action: dx={dx}, dy={dy}, click={click}")
            
        # Virtual SCADA actions
        elif cmd == "TOGGLE_PUMP":
            simulator_service.plc.pump_status = "OFF" if simulator_service.plc.pump_status == "ON" else "ON"
            simulator_service.timeline.append({
                "time": datetime_str(),
                "event": f"Pump switched {simulator_service.plc.pump_status} via Cloud",
                "severity": "info"
            })
        elif cmd == "CLOSE_VALVE":
            simulator_service.plc.inlet_valve_status = "CLOSED" if simulator_service.plc.inlet_valve_status == "OPEN" else "OPEN"
            simulator_service.timeline.append({
                "time": datetime_str(),
                "event": f"Valve switched {simulator_service.plc.inlet_valve_status} via Cloud",
                "severity": "info"
            })
        elif cmd in ["RESET_STATE", "UNLOCK"]:
            simulator_service.risk.risk_score = 12.0
            simulator_service.risk.risk_level = "LOW"
            simulator_service.emergency_active = False
            simulator_service.workstation_blocked = False
            simulator_service.pending_emergency_command = None
            simulator_service.integrity_status = "SAFE"
            simulator_service.learning_frozen = False
            simulator_service.compromise_type = "NONE"
            simulator_service.active_attack = "NONE"
            simulator_service.active_model_hash = simulator_service.trusted_snapshot
            simulator_service.timeline.append({
                "time": datetime_str(),
                "event": "System reset to baseline via Cloud",
                "severity": "info"
            })
        elif cmd.startswith("SIMULATE_ATTACK:"):
            attack_type = cmd.split(":")[1]
            simulator_service.active_attack = attack_type
            if attack_type == "RECON":
                simulator_service.risk.add_risk_event("Reconnaissance: Network port scanning", 20.0)
            elif attack_type == "CREDENTIALS":
                simulator_service.risk.add_risk_event("Brute-force credential assault", 35.0)
            elif attack_type == "LATERAL":
                simulator_service.risk.add_risk_event("Lateral Movement: Suspicious RPC connection", 50.0)
            elif attack_type == "PLC_ATTACK":
                simulator_service.plc.safety_override_active = True
                simulator_service.plc.pump_status = "OFF"
                simulator_service.plc.inlet_valve_status = "CLOSED"
                simulator_service.plc.outlet_valve_status = "CLOSED"
                simulator_service.risk.add_risk_event("PLC Attack: Remote register override", 80.0)
            elif attack_type == "MALWARE":
                simulator_service.risk.add_risk_event("Malware: Active file encryption payload", 90.0)
            elif attack_type == "INSIDER":
                simulator_service.risk.add_risk_event("Insider Threat: Unauthorized command executed", 30.0)
            elif attack_type == "EMERGENCY":
                await simulator_service.trigger_emergency()
            elif attack_type == "RECOVERY":
                simulator_service.recovery.start_recovery()
        elif cmd.startswith("RESPOND_EMERGENCY:"):
            decision = cmd.split(":")[1]
            action = simulator_service.pending_emergency_command or "Critical Override"
            if decision == "APPROVE":
                if action == "SHUTDOWN_PLANT":
                    simulator_service.plc.pump_status = "OFF"
                    simulator_service.plc.inlet_valve_status = "CLOSED"
                    simulator_service.plc.outlet_valve_status = "CLOSED"
                elif action == "TOGGLE_PUMP":
                    simulator_service.plc.pump_status = "OFF" if simulator_service.plc.pump_status == "ON" else "ON"
                elif action == "CLOSE_VALVE":
                    simulator_service.plc.inlet_valve_status = "CLOSED" if simulator_service.plc.inlet_valve_status == "OPEN" else "OPEN"
                simulator_service.timeline.append({
                    "time": datetime_str(),
                    "event": f"Mobile token validated. Command [{action}] APPROVED by Guardian.",
                    "severity": "high"
                })
            else:
                simulator_service.timeline.append({
                    "time": datetime_str(),
                    "event": f"Mobile token validated. Command [{action}] REJECTED.",
                    "severity": "high"
                })
            simulator_service.emergency_active = False
            simulator_service.workstation_blocked = False
            simulator_service.pending_emergency_command = None
            simulator_service.risk.risk_score = 12.0
            simulator_service.risk.risk_level = "LOW"
            simulator_service.integrity_status = "SAFE"
            simulator_service.learning_frozen = False
            simulator_service.compromise_type = "NONE"
            
        else:
            status = "failure"
            reason = f"Unknown command: {cmd}"
    except Exception as e:
        status = "failure"
        reason = str(e)
        logger.error(f"[AGENT] Error executing command {cmd}: {e}")
        
    response = {
        "type": "COMMAND_RESPONSE",
        "status": status,
        "command": cmd,
        "reason": reason,
        "timestamp": str(int(time.time()))
    }
    await send_to_cloud(response)

async def start_agent():
    logger.info("[AGENT] Starting local simulator loops...")
    await simulator_service.start()
    
    retry_delay = 1
    while True:
        try:
            logger.info(f"[AGENT] Connecting to Cloud Server at {CLOUD_WS_URL}...")
            async with websockets.connect(CLOUD_WS_URL) as ws:
                global websocket_client
                websocket_client = ws
                retry_delay = 1
                logger.info("[AGENT] Connected to Cloud Server successfully.")
                
                # Start heartbeat and telemetry tasks
                heartbeat_task = asyncio.create_task(send_heartbeats())
                telemetry_task = asyncio.create_task(send_telemetry())
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "COMMAND":
                            asyncio.create_task(handle_agent_command(data))
                    except Exception as e:
                        logger.error(f"[AGENT] Error parsing message: {e}")
                        
                heartbeat_task.cancel()
                telemetry_task.cancel()
        except Exception as e:
            logger.error(f"[AGENT] Connection error: {e}. Reconnecting in {retry_delay}s...")
            # Trigger Auto-Lockdown on connection loss!
            asyncio.create_task(check_connection_loss_lockdown())
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 15) # Cap reconnection sleep at 15s

async def send_heartbeats():
    while True:
        try:
            await send_to_cloud("heartbeat")
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[AGENT] Heartbeat error: {e}")

async def send_telemetry():
    while True:
        try:
            host_telemetry = host_monitor.collect_telemetry()
            cpu_val = host_telemetry["host_cpu"]
            cpu_status = "normal" if cpu_val < 50 else "high" if cpu_val < 85 else "critical"
            
            network_status = "active"
            if simulator_service.comms.get_active_route() == "DISRUPTED":
                network_status = "disconnected"
                
            user_status = "logged-in" if host_telemetry["user_active"] else "logged-out"
            risk_status = simulator_service.risk.risk_level.lower()
            
            payload = {
                "type": "TELEMETRY_STATUS",
                "cpu": cpu_status,
                "network": network_status,
                "user": user_status,
                "risk": risk_status,
                "timestamp": str(int(time.time()))
            }
            await send_to_cloud(payload)
            
            # Auto-Lockdown Check if suspicious behavior detected (Risk score > 75 or critical threats)
            if simulator_service.risk.risk_score > 75.0 or simulator_service.active_attack in ["RANSOMWARE", "MALWARE"]:
                alert = {
                    "type": "THREAT_ALERT",
                    "deviceId": DEVICE_ID,
                    "severity": "CRITICAL",
                    "details": f"Suspicious activity detected. Active threat: {simulator_service.active_attack}. Risk: {simulator_service.risk.risk_score}%",
                    "timestamp": str(int(time.time()))
                }
                await send_to_cloud(alert)
                await execute_lock_system()
                
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[AGENT] Telemetry send error: {e}")

async def check_connection_loss_lockdown():
    # If not already blocked, trigger lock
    if not simulator_service.workstation_blocked:
        logger.warning("[AGENT] Cloud connection lost. Triggering Auto-Lockdown.")
        await execute_lock_system()
