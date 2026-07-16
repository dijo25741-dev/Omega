import time
import json
import logging
from typing import Dict
from fastapi import WebSocket
from app.security.command_verifier import sign_command, generate_command_token

logger = logging.getLogger("omega.cloud_agent_bridge")

# Global reference to active connections and state tracking
connected_devices: Dict[str, WebSocket] = {}
device_heartbeats: Dict[str, float] = {}
registered_devices: Dict[str, Dict] = {}
command_history = []

async def send_command_to_agent_by_id(device_id: str, command: str) -> bool:
    """
    Formulates, signs, and dispatches a command payload to the specified agent.
    """
    global connected_devices
    if device_id not in connected_devices:
        logger.error(f"[CLOUD] Cannot dispatch command '{command}': Laptop Agent '{device_id}' is not connected.")
        return False
        
    ws = connected_devices[device_id]
    
    timestamp = str(int(time.time()))
    signature = sign_command(command, timestamp)
    token = generate_command_token()
    
    payload = {
        "type": "COMMAND",
        "command": command,
        "token": token,
        "signature": signature,
        "timestamp": timestamp
    }
    
    try:
        await ws.send_text(json.dumps(payload))
        logger.info(f"[CLOUD] Command '{command}' successfully dispatched to Agent '{device_id}'.")
        return True
    except Exception as e:
        logger.error(f"[CLOUD] Failed to send command to Agent '{device_id}' over WebSocket: {e}")
        return False

async def send_command_to_agent(command: str) -> bool:
    """
    Default dispatch using fallback device id 'omega-001'.
    """
    return await send_command_to_agent_by_id("omega-001", command)
