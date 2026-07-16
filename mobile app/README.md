# Omega Trust & Recovery System

The **Omega Trust & Recovery System** acts as the human trust layer of a cyber immune system for critical infrastructure. During high-risk attacks, it isolates the compromised workstation and dynamically delegates authentication token authority to a cryptographically bound mobile device.

## Project Structure

```text
d:/OMEGA/
├── backend/
│   ├── main.py               # FastAPI backend with websockets & state logic
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Dark-industrial SCADA dashboard UI
│   │   ├── index.css         # Tailwind v4 import & custom CSS animations
│   │   └── main.jsx          # React app entry point
│   ├── index.html
│   ├── vite.config.js        # Vite + Tailwind configuration
│   └── package.json
└── mobile_guardian/
    └── lib/
        └── main.dart         # Flutter Mobile Guardian application
```

## Quick Start Setup

### 1. Launch backend API
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Launch SCADA Dashboard
```bash
cd frontend
npm install
npm run dev
```

### 3. Open Dashboard in Browser
Navigate to `http://localhost:5173`.

---

## Simulated Hackathon Flow
1. **Normal Flow**: Click `TOGGLE PUMP` or `TOGGLE VALVE` to observe status updates and live metrics.
2. **AI Protection Sandbox**: Test value validation by putting `95` or using an untrusted PLC source at the bottom panels.
3. **Attack State**: Click the red `ATTACK STATE` header button to simulate model weight tampering.
4. **Emergency lockout**: Click `CRITICAL SHUTDOWN` on the dashboard. The system locks down, transferring all validation tasks to the Mobile Guardian app.
5. **Mobile Authorization**: Log in to the Guardian App with operator credentials (`admin` / `omega2026`) and Approve or Reject the pending action to recover control.
