# Omega Intelligence Core

**Omega** is an Invisible, Self-Protecting AI Cyber Immune System for Critical National Infrastructure (CNI). The backend serves as the core intelligence unit of the immune system. It runs in passive observation mode, monitoring industrial networks and answering three crucial questions every second:
1. **What is happening?** (Dynamic profiling & anomaly detection)
2. **What will happen next?** (Machine learning threat prediction & cyber kill chain mapping)
3. **Should the infrastructure trust this activity?** (Dynamic device/operator trust scoring & contextual validation)

Omega does **NOT** directly control Programmable Logic Controllers (PLCs). Instead, it acts as a contextual validation shield and security analyst.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, Python 3.10
- **AI Core:** Scikit-learn (Random Forest), Pandas, NumPy, NetworkX (Topology Modeling)
- **Database:** SQLite (Real-time telemetry, audits, and alerts persistence)
- **Visualization:** Plotly, Matplotlib (Plot summaries & explanation breakdowns)
- **Testing:** PyTest, FastAPI TestClient

---

## 📁 Repository Structure
```
backend/
├── app.py                      # Main entrypoint & startup/shutdown registration
├── config.py                   # Central settings, constants & topological graph setup
├── requirements.txt            # Python environment packages
├── Dockerfile                  # Slim-based docker configuration
├── docker-compose.yml          # Container configuration for quick deploy
│
├── api/                        # REST endpoint routers
│   ├── command.py              # Command validations & audit logs
│   ├── dashboard.py            # Unified frontend dashboard queries
│   ├── explain.py              # XAI narrative text & contribution charts
│   ├── graph.py                # NetworkX topology edits & Plotly representations
│   ├── predict.py              # Raw ML inference & retraining triggers
│   └── risk.py                 # Live risk aggregates & historical series
│
├── ai/                         # Security decision engines
│   ├── command_guardian.py     # Context-aware physical & operational rules
│   ├── explainable_ai.py       # Narrative generation & chart export helpers
│   ├── infrastructure_learning.py # Parameter envelope estimations & Z-Score anomaly engine
│   ├── risk_engine.py          # Dynamic risk aggregator
│   └── threat_prediction.py    # Random Forest ML wrapper & next-action mapping
│
├── graph/
│   └── graph_builder.py        # NetworkX asset management & Plotly exports
│
├── models/
│   └── ml_models.py            # RF training & synthetic telemetry generators
│
├── database/
│   └── database.py             # SQLite helper scripts & storage schemas
│
├── simulator/
│   └── plc_data_generator.py   # Stochastic normal vs attack telemetry simulation loop
│
└── tests/
    └── test_core.py            # Automated backend unit tests
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ installed locally OR Docker Desktop.

### Method 1: Local Installation (Virtual Environment)
1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI server:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```
4. **Access the application:**
   - Interactive Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Alternative ReDoc documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Method 2: Containerized Installation (Docker)
1. **Build and start the application using docker-compose:**
   ```bash
   docker-compose up --build
   ```
2. **Access Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing
We use `pytest` for automated test coverage checking prediction indices, risk engine weights, sequence logic, and router responses:

Run the test suite using:
```bash
python -m pytest tests/
```

---

## 🛡️ Core Security Architecture & API Specifications

### 1. Dynamic Behavior Profiling (`ai/infrastructure_learning.py`)
Tracks rolling distributions of temperature, pressure, flow, voltage, and current on a per-device basis using Welford's algorithm. Evaluates incoming parameters using Z-scores:
- Z-score > 3.0 triggers an anomaly warning, lowering the device's trust level.
- Operator trust is dynamically tracked and decays upon failed logins or command validation blocks.

### 2. Threat Stage Classification (`ai/threat_prediction.py`)
A Random Forest Classifier trained on high-fidelity synthetic telemetry datasets predicting attack lifecycle stages:
- `Normal`, `Reconnaissance` (port scanning), `Credential Theft` (brute force), `Privilege Escalation` (exploit payloads), `Lateral Movement` (pivot network traffic), `PLC Targeting` (malicious command sequencing), and `Ransomware` (high-workstation CPU/memory load and file access latency).

### 3. Risk Quantification Engine (`ai/risk_engine.py`)
Compiles threat stage, Z-score anomalies, CPU/Memory health, operator authorization, network delays, and historical incidents into a 0-100 score:
- **Low (0-25)** | **Medium (26-50)** | **High (51-75)** | **Critical (76-100)**

### 4. Mission-Aware Command Guardian (`ai/command_guardian.py`)
Intercepts operator controls (e.g. `SHUTDOWN_PUMP`, `CLOSE_VALVE`) and performs logical verification:
- Checks if operator is trusted.
- Verifies if command violates physical safety bounds (e.g. blocking pump shutdown if temperature > 85°C, or closing valves if line pressure > 5.5 bar).
- Verifies sequence transitions and blocks anomalous control sequences.
- Bypasses rules if scheduled maintenance is active on the device.

### 5. Simulator Control (`simulator/plc_data_generator.py`)
Generates 1-second telemetry frames. Use the API to alter modes to test the immune system behavior:
- `NORMAL`: Steady operating variations.
- `ATTACK_RECON`: Scans, higher packet rates.
- `ATTACK_CREDENTIALS`: Failed login attempts.
- `ATTACK_PLC`: Destructive command injections, parameter manipulations.
- `ATTACK_RANSOMWARE`: System encryption loads, high latency.

---

## 📊 Consolidated API Endpoints

- **`GET /simulate/status`**: Uptime, mode, and latest telemetry frames.
- **`POST /simulate/mode`**: Toggle simulation scenarios (`NORMAL`, `ATTACK_RECON`, `ATTACK_CREDENTIALS`, `ATTACK_PLC`, `ATTACK_RANSOMWARE`).
- **`GET /risk`**: Fetch latest aggregated risk ratings.
- **`POST /predict`**: Perform ML classification on raw payload structures.
- **`POST /validate-command`**: Validate security instructions against plant rules.
- **`GET /graph`**: Get NetworkX topology nodes and edge listings.
- **`GET /explanation`**: Obtain latest decision summaries and base64 factor contribution charts.
- **`GET /dashboard`**: Consolidated endpoint for single-call React dashboard integrations.
- **`POST /predict/retrain`**: Trigger manual classifier retraining.
