import logging
import json
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from app.config import settings
from app.database import engine, Base
from app.services.simulator import simulator_service
from app.websocket.manager import manager
from app.audit.logger import log_event

# Configure logging format and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("omega.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifespan events.
    Automatically creates database tables and kicks off the background simulation loop.
    """
    logger.info("Starting Omega Cyber Resilience Central Cloud Server...")
    
    # 1. Automatically create database tables if they do not exist
    async with engine.begin() as conn:
        logger.info("Executing database schema synchronization...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")

    # 2. Write startup event to audit logs
    await log_event(
        event="Omega Core Engine Bootstrapped",
        module="SYSTEM",
        user="SYSTEM",
        decision="BOOT",
        reason="Server initialization completed successfully",
        confidence_score=1.0,
        status="SUCCESS"
    )

    # 3. Simulator loop is disabled on cloud server (runs on the Agent client instead)
    # await simulator_service.start()

    yield

    # Shutdown events
    logger.info("Shutting down Omega Cyber Resilience Central Cloud Server...")
    await log_event(
        event="Omega Core Engine Terminated",
        module="SYSTEM",
        user="SYSTEM",
        decision="SHUTDOWN",
        reason="Server shutdown requested",
        confidence_score=1.0,
        status="SUCCESS"
    )
    # await simulator_service.stop()
    logger.info("Omega Clean shutdown completed.")

# Initialize FastAPI App with lifespan manager
app = FastAPI(
    title=settings.APP_NAME,
    description="Invisible cyber resilience layer for Critical National Infrastructure SCADA systems.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and Mount Routers
from app.routers.plant import router as plant_router
from app.routers.plc import router as plc_router
from app.routers.communication import router as comm_router
from app.routers.security import router as sec_router
from app.routers.risk import router as risk_router
from app.routers.recovery import router as rec_router
from app.routers.audit import router as audit_router
from app.routers.health import router as health_router
from app.routers.attack import router as attack_router
from app.routers.ai import router as ai_router
from app.routers.trust import router as trust_router

app.include_router(plant_router)
app.include_router(plc_router)
app.include_router(comm_router)
app.include_router(sec_router)
app.include_router(risk_router)
app.include_router(rec_router)
app.include_router(audit_router)
app.include_router(health_router)
app.include_router(attack_router)
app.include_router(ai_router)
app.include_router(trust_router)

# WebSocket Real-Time Broadcast Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time telemetry and resilience state streaming channel."""
    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection, handle client ping/pong messages
            data = await websocket.receive_text()
            # If the frontend sends any commands over WebSocket, they could be parsed here
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error on client socket: {e}")
        manager.disconnect(websocket)

# Pydantic models for mobile app integration
class CommandBody(BaseModel):
    deviceId: str
    command: str

class RegisterBody(BaseModel):
    deviceId: str
    owner: str

JWT_SECRET = "supersecretkey"
ALGORITHM = "HS256"

@app.post("/register-device")
def register_device(body: RegisterBody):
    import app.services.cloud_agent_bridge as bridge
    bridge.registered_devices[body.deviceId] = {
        "owner": body.owner,
        "registered_at": time.time()
    }
    logger.info(f"Registered device: {body.deviceId}")
    return {"status": "registered", "deviceId": body.deviceId}

@app.get("/device-status/{device_id}")
def get_device_status(device_id: str):
    import app.services.cloud_agent_bridge as bridge
    is_connected = device_id in bridge.connected_devices
    last_seen = bridge.device_heartbeats.get(device_id, 0)
    now = time.time()
    
    if is_connected and (now - last_seen < 15.0):
        return {"deviceId": device_id, "status": "online", "last_seen": last_seen}
    else:
        if device_id in bridge.connected_devices:
            del bridge.connected_devices[device_id]
        return {"deviceId": device_id, "status": "offline", "last_seen": last_seen}

@app.post("/send-command")
async def send_command(body: CommandBody, authorization: str = Header(None)):
    import app.services.cloud_agent_bridge as bridge
    
    if authorization:
        try:
            token = authorization.split(" ")[1] if " " in authorization else authorization
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            logger.info(f"Command authorized for user: {payload.get('sub')}")
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    else:
        logger.warning("Command received without authorization header. Permitting in development mode.")

    device_id = body.deviceId
    command = body.command

    status_info = get_device_status(device_id)
    if status_info["status"] == "online":
        success = await bridge.send_command_to_agent_by_id(device_id, command)
        if success:
            bridge.command_history.append({
                "deviceId": device_id,
                "command": command,
                "timestamp": time.time(),
                "status": "relayed"
            })
            logger.info(f"Relayed command '{command}' to device '{device_id}'")
            return {"status": "sent", "command": command}
        else:
            return {"status": "failed to send"}

    logger.warning(f"Device '{device_id}' is offline. Command '{command}' not sent.")
    return {"status": "device offline"}

@app.get("/command-history")
def get_command_history():
    import app.services.cloud_agent_bridge as bridge
    return {"history": bridge.command_history}

# WebSocket Laptop Agent Connection Endpoint
@app.websocket("/ws/{device_id}")
async def agent_websocket_endpoint(websocket: WebSocket, device_id: str):
    """Secure tunnel for the Laptop Agent to report telemetry/logs and receive commands."""
    import app.services.cloud_agent_bridge as bridge
    logger.info(f"[CLOUD] Laptop Agent attempting to connect via /ws/{device_id}...")
    await websocket.accept()
    bridge.connected_devices[device_id] = websocket
    bridge.device_heartbeats[device_id] = time.time()
    logger.info(f"[CLOUD] Laptop Agent connected successfully: {device_id}")
    
    try:
        while True:
            message_str = await websocket.receive_text()
            if message_str == "heartbeat":
                bridge.device_heartbeats[device_id] = time.time()
            else:
                try:
                    data = json.loads(message_str)
                    msg_type = data.get("type")
                    
                    if msg_type == "TELEMETRY_STATUS":
                        await manager.broadcast(data)
                    elif msg_type == "THREAT_ALERT":
                        await log_event(
                            event="Agent Threat Alert",
                            module="SECURITY",
                            user=data.get("deviceId", device_id),
                            decision="ALERT",
                            reason=data.get("details", "Suspicious activity detected on agent"),
                            confidence_score=1.0,
                            status="WARNING"
                        )
                        await manager.broadcast(data)
                    elif msg_type == "TELEMETRY":
                        sim_data = data.get("data", {})
                        # Update local simulator_service state cache
                        simulator_service.risk.risk_score = sim_data.get("risk_value", 12.0)
                        simulator_service.risk.risk_level = sim_data.get("risk_level", "LOW")
                        simulator_service.plc.pump_status = sim_data.get("pump_status", "ON")
                        simulator_service.plc.inlet_valve_status = sim_data.get("valve_status", "OPEN")
                        simulator_service.plant.water_level = sim_data.get("tank_level", 450.0)
                        simulator_service.plant.flow_rate = sim_data.get("flow_rate", 15.0)
                        simulator_service.integrity_status = sim_data.get("integrity_status", "SAFE")
                        simulator_service.learning_frozen = sim_data.get("learning_frozen", False)
                        simulator_service.active_model_hash = sim_data.get("active_model_hash", "")
                        simulator_service.emergency_active = sim_data.get("emergency_active", False)
                        simulator_service.workstation_blocked = sim_data.get("workstation_blocked", False)
                        simulator_service.pending_emergency_command = sim_data.get("pending_emergency_command", None)
                        simulator_service.compromise_type = sim_data.get("compromise_type", "NONE")
                        simulator_service.timeline = sim_data.get("timeline", [])
                        
                        await manager.broadcast(data)
                    elif msg_type == "COMMAND_RESPONSE":
                        status_val = data.get("status")
                        cmd_val = data.get("command")
                        reason_val = data.get("reason", "")
                        await log_event(
                            event=f"Agent Command Executed: {cmd_val}",
                            module="SYSTEM",
                            user="AGENT",
                            decision="EXECUTE",
                            reason=reason_val if status_val == "failure" else "Command completed successfully",
                            confidence_score=1.0,
                            status="SUCCESS" if status_val == "success" else "FAILURE"
                        )
                        await manager.broadcast(data)
                except Exception as parse_err:
                    logger.error(f"[CLOUD] Error parsing agent message: {parse_err}")
    except WebSocketDisconnect:
        logger.warning(f"[CLOUD] Laptop Agent disconnected: {device_id}")
    except Exception as e:
        logger.error(f"[CLOUD] Agent WebSocket error on {device_id}: {e}")
    finally:
        bridge.connected_devices.pop(device_id, None)
        bridge.device_heartbeats.pop(device_id, None)

from fastapi.staticfiles import StaticFiles
import os
import sys

# Mount screenshots static files folder
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(static_dir, exist_ok=True)
placeholder_file = os.path.join(static_dir, "placeholder.png")
if not os.path.exists(placeholder_file):
    try:
        with open(placeholder_file, "wb") as f:
            f.write(b"")
    except Exception:
        pass

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount React static files build folder
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    frontend_dist = os.path.join(sys._MEIPASS, "frontend/dist")
else:
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    logger.info(f"Frontend static files mounted from {frontend_dist}")
else:
    logger.warning(f"Frontend static files folder not found at {frontend_dist}. Running in API-only mode.")
