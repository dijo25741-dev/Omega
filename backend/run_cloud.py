import uvicorn
import sys
import os

# Add parent directory of app to path to ensure all imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    print("[*] Starting Centralized Cloud Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
