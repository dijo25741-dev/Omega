import hmac
import hashlib
import time
import jwt
import logging
from app.config import settings

logger = logging.getLogger("omega.security.command_verifier")

# Default to Settings Secret Key, fallback to fallback value
SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"

def sign_command(command: str, timestamp: str) -> str:
    """
    Generates an HMAC-SHA256 signature for the command and timestamp.
    """
    message = f"{command}:{timestamp}"
    signature = hmac.new(SECRET_KEY.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature

def verify_command_signature(command: str, timestamp: str, signature: str) -> bool:
    """
    Verifies that the HMAC-SHA256 signature is valid and has not expired (anti-replay).
    """
    try:
        # Check for replay attacks: signature must be within a 60-second window
        current_time = int(time.time())
        cmd_time = int(timestamp)
        if abs(current_time - cmd_time) > 60:
            logger.error(f"Command signature verification failed: Timestamp expired (drift: {current_time - cmd_time}s).")
            return False
            
        expected_signature = sign_command(command, timestamp)
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error validating signature: {e}")
        return False

def generate_command_token() -> str:
    """
    Generates a secure JWT token authorizing cloud-mediated commands.
    """
    payload = {
        "sub": "cloud-server",
        "role": "cloud",
        "exp": time.time() + 60  # Valid for 60 seconds
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_command_token(token: str) -> bool:
    """
    Decodes and verifies the JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("role") == "cloud":
            return True
        logger.error(f"Command token verification failed: Invalid role '{payload.get('role')}'")
        return False
    except jwt.ExpiredSignatureError:
        logger.error("Command token verification failed: JWT has expired.")
        return False
    except jwt.InvalidTokenError as e:
        logger.error(f"Command token verification failed: Invalid JWT token: {e}")
        return False
