import React, { useState, useEffect, useRef } from "react";
import { 
  Shield, 
  Activity, 
  Database, 
  Wifi, 
  WifiOff, 
  AlertTriangle, 
  Lock, 
  RotateCcw, 
  Cpu, 
  Layers, 
  Smartphone,
  CheckCircle,
  XCircle,
  Terminal,
  Fingerprint
} from "lucide-react";

export default function App() {
  const [wsStatus, setWsStatus] = useState("DISCONNECTED");
  const [telemetry, setTelemetry] = useState({
    risk_level: "LOW",
    risk_value: 12,
    pump_status: "ON",
    valve_status: "OPEN",
    tank_level: 68.5,
    flow_rate: 14.2,
    integrity_status: "SAFE",
    learning_frozen: false,
    active_model_hash: "sha256_9f86...",
    emergency_active: false,
    workstation_blocked: false,
    pending_emergency_command: null,
    compromise_type: "NONE",
    timeline: [],
    ai_explanation: {
      action: "MONITORING",
      reason: [],
      confidence: 99.8
    },
    host_monitor: {
      host_cpu: 12.5,
      host_memory: 38.2,
      total_processes: 115,
      new_processes: [],
      total_connections: 42,
      outbound_connections: 3,
      file_changes: [],
      device_health: 100.0,
      user_active: true
    }
  });

  const [sensorValInput, setSensorValInput] = useState("45.0");
  const [learningResult, setLearningResult] = useState(null);

  const [provenanceSource, setProvenanceSource] = useState("OT_SENSOR_PLC_1");
  const [provenanceHash, setProvenanceHash] = useState("sha256_b3a19d");
  const [provenanceResult, setProvenanceResult] = useState(null);

  const [cmdError, setCmdError] = useState("");
  const [wsLogs, setWsLogs] = useState([]);

  const wsRef = useRef(null);

  useEffect(() => {
    connectWS();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const addWsLog = (direction, msg) => {
    const timeStr = new Date().toLocaleTimeString();
    setWsLogs(prev => [{ time: timeStr, dir: direction, msg }, ...prev].slice(0, 20));
  };

  const connectWS = () => {
    setWsStatus("CONNECTING");
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus("CONNECTED");
      addWsLog("SYSTEM", "WebSocket channel SECURED (AES-GCM)");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        addWsLog("INBOUND", `Type: ${payload.type}`);
        if (payload.type === "TELEMETRY") {
          setTelemetry(payload.data);
        }
      } catch (err) {
        console.error("WS parse error", err);
      }
    };

    ws.onclose = () => {
      setWsStatus("DISCONNECTED");
      addWsLog("SYSTEM", "WebSocket disconnected. Reconnection pending...");
      setTimeout(connectWS, 3000);
    };
  };

  const triggerAction = async (actionType) => {
    if (telemetry.workstation_blocked) {
      setCmdError("IMMUNE SHIELD: Command rejected. Workstation lock active.");
      addWsLog("OUTBOUND", `BLOCKED CMD: ${actionType}`);
      return;
    }
    setCmdError("");
    addWsLog("OUTBOUND", `EXEC CMD: ${actionType}`);
    try {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type: actionType, payload: {} })
      });
      const data = await res.json();
      if (res.status === 403) {
        setCmdError(data.detail);
      }
    } catch (e) {
      setCmdError("API Connection failure.");
    }
  };

  const triggerAttackScenario = async (type) => {
    addWsLog("SYSTEM", `Simulating Attack Vector: ${type}`);
    try {
      let url = "/api/simulate-attack";
      let body = { type };
      
      if (type === "RECON") url = "/attack/recon";
      else if (type === "CREDENTIALS") url = "/attack/credentials";
      else if (type === "LATERAL") url = "/attack/lateral";
      else if (type === "PLC_ATTACK") url = "/attack/plc";
      else if (type === "MALWARE") url = "/attack/malware";
      else if (type === "INSIDER_THREAT") url = "/attack/insider";
      else if (type === "EMERGENCY") url = "/attack/emergency";
      else if (type === "RECOVERY") url = "/attack/recovery";
      
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
    } catch (e) {
      console.error(e);
    }
  };

  const submitGuardianDecision = async (decision) => {
    addWsLog("SYSTEM", `Submitting Operator Recovery Signature: ${decision}`);
    try {
      await fetch("/api/respond-emergency", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision,
          token: "virtual_bypass"
        })
      });
    } catch (e) {
      console.error(e);
    }
  };

  const resetState = async () => {
    addWsLog("SYSTEM", "Sending global baseline reset signal...");
    try {
      await fetch("/api/reset", { method: "POST" });
      setLearningResult(null);
      setProvenanceResult(null);
      setCmdError("");
    } catch (e) {
      console.error(e);
    }
  };

  const handleLearnData = async () => {
    setLearningResult({ loading: true });
    try {
      const res = await fetch("/api/learn-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: { val: parseFloat(sensorValInput) } })
      });
      const data = await res.json();
      setLearningResult(data);
    } catch (e) {
      setLearningResult({ status: "REJECTED", reason: "API failure" });
    }
  };

  const handleValidateData = async () => {
    setProvenanceResult({ loading: true });
    try {
      const res = await fetch("/api/validate-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: provenanceSource,
          data_hash: provenanceHash,
          payload: {}
        })
      });
      const data = await res.json();
      setProvenanceResult(data);
    } catch (e) {
      setProvenanceResult({ trusted: false, reason: "API failure" });
    }
  };

  return (
    <main className="min-h-screen bg-[#f8fafc] p-4 md:p-6 text-slate-800 relative">
      
      {/* GLOW TOP SHIELD */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />

      {/* HEADER */}
      <header className="border border-slate-200 bg-white p-4 flex flex-wrap justify-between items-center mb-6 rounded shadow-md relative overflow-hidden">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-50 rounded border border-cyan-200">
            <Shield className="w-8 h-8 text-cyan-600 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-widest text-slate-900 uppercase font-mono">
              Omega Trust & Recovery Control Center
            </h1>
            <p className="text-[10px] text-slate-500 tracking-widest font-mono">
              HUMAN TRUST LAYER OF AN AI CYBER IMMUNE SYSTEM FOR CRITICAL OT
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-3 lg:mt-0 flex-wrap">
          {/* WS Status */}
          <div className="flex items-center gap-2 border border-slate-200 px-3 py-1.5 rounded bg-slate-50 text-[10px] font-mono">
            {wsStatus === "CONNECTED" ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                <span className="text-emerald-600 font-bold">CHANNEL SECURE</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-red-600 font-bold">OFFLINE</span>
              </>
            )}
          </div>

          {/* Active Mode */}
          <div className="flex items-center gap-2 border border-slate-200 px-3 py-1.5 rounded bg-slate-50 text-[10px] font-mono">
            <span className="text-slate-400">MODE:</span>
            {telemetry.workstation_blocked ? (
              <span className="text-red-600 font-extrabold animate-pulse">EMERGENCY LOCKOUT</span>
            ) : telemetry.risk_level === "MEDIUM" || telemetry.risk_level === "HIGH" ? (
              <span className="text-amber-600 font-bold">PROTECTION</span>
            ) : (
              <span className="text-emerald-600 font-bold">OBSERVATION</span>
            )}
          </div>

          {/* Active Controller */}
          <div className="flex items-center gap-2 border border-slate-200 px-3 py-1.5 rounded bg-slate-50 text-[10px] font-mono">
            <span className="text-slate-400">CONTROLLER:</span>
            {telemetry.workstation_blocked ? (
              <span className="text-red-650 font-extrabold">MOBILE GUARDIAN</span>
            ) : (
              <span className="text-slate-700 font-bold">SCADA HMI CONSOLE</span>
            )}
          </div>

          <button
            onClick={resetState}
            className="flex items-center gap-1.5 border border-slate-200 hover:border-slate-350 bg-white px-3 py-1.5 rounded text-[11px] font-mono hover:bg-slate-50 transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            RESET SYSTEM
          </button>
        </div>
      </header>

      {/* DYNAMIC SCENARIO PANEL */}
      <section className="border border-slate-200 bg-white p-4 rounded mb-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
          <h2 className="text-xs font-bold text-slate-700 tracking-widest uppercase font-mono flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" /> CNI CYBER ATTACK & DEFENSE SIMULATOR
          </h2>
          <span className="text-[10px] text-slate-400 font-mono">CLICK VECTOR TO SIMULATE</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          <button
            onClick={() => resetState()}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "NONE" ? "border-emerald-400 bg-emerald-50 text-emerald-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-emerald-200"
            }`}
          >
            <div className="font-bold">✓ Normal Operations</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Clear all active threat payloads</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("RECON")}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "RECON" ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-red-200"
            }`}
          >
            <div className="font-bold">1. Reconnaissance</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Port scans & network sweeps</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("CREDENTIALS")}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "CREDENTIALS" ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-red-200"
            }`}
          >
            <div className="font-bold">2. Credential Attack</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Multiple brute-force logins</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("LATERAL")}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "LATERAL" ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-red-200"
            }`}
          >
            <div className="font-bold">3. Lateral Movement</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Internal pivots & remote logins</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("PLC_ATTACK")}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "PLC_ATTACK" ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-red-200"
            }`}
          >
            <div className="font-bold">4. PLC Attack</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Force shutdowns & valve limits</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("MALWARE")}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "MALWARE" ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-red-200"
            }`}
          >
            <div className="font-bold">5. Malware load</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Encrypt volume & spike system CPU</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("INSIDER_THREAT")}
            className={`py-2 px-3 border rounded font-mono text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "INSIDER_THREAT" ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-red-200"
            }`}
          >
            <div className="font-bold">6. Insider Threat</div>
            <div className="text-[9px] text-slate-450 mt-0.5">Edits outside maintenance window</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("EMERGENCY")}
            className="py-2 px-3 border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 rounded font-mono text-xs text-left transition cursor-pointer"
          >
            <div className="font-bold">7. Force Emergency</div>
            <div className="text-[9px] text-red-650 mt-0.5">Trigger immediate lockout trip</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("RECOVERY")}
            className="py-2 px-3 border border-emerald-250 bg-emerald-50 hover:bg-emerald-100 text-emerald-850 rounded font-mono text-xs text-left transition cursor-pointer"
          >
            <div className="font-bold">8. Self-Healing Recovery</div>
            <div className="text-[9px] text-emerald-650 mt-0.5">Re-image weights and boot disk</div>
          </button>
        </div>
      </section>

      {/* CORE DISPLAY (GRID) */}
      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* SCADA WORKSTATION */}
        <div className="flex-1 space-y-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* PHYSICAL SCADA LOOP */}
            <section className="border border-slate-200 bg-white rounded p-5 relative overflow-hidden flex flex-col justify-between min-h-[360px] shadow-md">
              {telemetry.workstation_blocked && (
                <div className="absolute inset-0 bg-red-50/90 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center p-4 text-center">
                  <Lock className="w-12 h-12 text-red-600 mb-2 animate-bounce" />
                  <span className="font-mono text-xs font-bold text-red-700 tracking-wider">
                    CONSOLE INTERLOCK ACTIVE
                  </span>
                  <span className="text-[10px] text-slate-500 mt-1 max-w-[200px]">
                    Authority transferred to Mobile Guardian
                  </span>
                </div>
              )}

              <div>
                <h3 className="text-xs font-bold text-slate-700 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2 font-mono">
                  <Activity className="w-4 h-4 text-cyan-600" /> PHYSICAL SCADA LOOP
                </h3>

                <div className="flex items-center justify-around my-6">
                  {/* Fluid Level Tank */}
                  <div className="relative w-28 h-44 border border-slate-200 bg-slate-50 rounded-b-xl overflow-hidden flex flex-col justify-end">
                    <div 
                      className="bg-cyan-500/20 border-t border-cyan-500 w-full relative liquid-wave transition-all duration-1000"
                      style={{ height: `${telemetry.tank_level}%` }}
                    >
                      <div className="absolute top-2 left-0 right-0 text-center font-mono text-[11px] font-bold text-cyan-700 drop-shadow">
                        {telemetry.tank_level}%
                      </div>
                    </div>
                    <div className="absolute top-2 left-2 right-2 text-center text-[9px] text-slate-400 font-mono">
                      PLANT T-102
                    </div>
                  </div>

                  {/* Telemetry details */}
                  <div className="flex flex-col gap-3 font-mono text-xs">
                    <div>
                      <span className="text-slate-500 block text-[10px]">INTAKE PUMP</span>
                      <span className={`font-bold px-2 py-0.5 rounded text-[10px] inline-block mt-0.5 ${telemetry.pump_status === "ON" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
                        {telemetry.pump_status}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">DISCHARGE VALVE</span>
                      <span className={`font-bold px-2 py-0.5 rounded text-[10px] inline-block mt-0.5 ${telemetry.valve_status === "OPEN" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
                        {telemetry.valve_status}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">DISCHARGE FLOW</span>
                      <span className="text-sm font-bold text-cyan-600">{telemetry.flow_rate} m³/h</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Console operations */}
              <div className="border-t border-slate-100 pt-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => triggerAction("TOGGLE_PUMP")}
                    className="flex-1 py-2 px-3 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-mono text-[10px] font-bold cursor-pointer transition rounded"
                  >
                    TOGGLE PUMP
                  </button>
                  <button
                    onClick={() => triggerAction("CLOSE_VALVE")}
                    className="flex-1 py-2 px-3 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-mono text-[10px] font-bold cursor-pointer transition rounded"
                  >
                    TOGGLE VALVE
                  </button>
                </div>
                
                {cmdError && (
                  <p className="mt-3 text-red-600 font-mono text-[10px] leading-tight border border-red-200 p-2 rounded bg-red-50">
                    {cmdError}
                  </p>
                )}
              </div>
            </section>

            {/* CYBER RISK / AI EXPLAINABLE CORE */}
            <section className="border border-slate-200 bg-white rounded p-5 flex flex-col justify-between min-h-[360px] shadow-md">
              <div>
                <h3 className="text-xs font-bold text-slate-700 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2 font-mono">
                  <Cpu className="w-4 h-4 text-cyan-600" /> RISK & XAI TRUST ENGINE
                </h3>

                <div className="mb-4">
                  <div className="flex justify-between text-[10px] font-mono mb-1 text-slate-500">
                    <span>CYBER IMMUNITY RISK METER</span>
                    <span>{telemetry.risk_value}%</span>
                  </div>
                  <div className="h-3.5 bg-slate-100 rounded overflow-hidden flex p-[2px] border border-slate-200">
                    <div 
                      className={`h-full rounded-sm transition-all duration-500 ${
                        telemetry.risk_level === "LOW" ? "bg-emerald-500 glow-green" :
                        telemetry.risk_level === "MEDIUM" ? "bg-yellow-500 glow-yellow" :
                        telemetry.risk_level === "HIGH" ? "bg-orange-500 glow-orange" :
                        "bg-red-500 glow-red"
                      }`} 
                      style={{ width: `${telemetry.risk_value}%` }} 
                    />
                  </div>
                </div>

                {/* XAI */}
                <div className="bg-slate-50 border border-slate-100 p-3 rounded font-mono text-[11px] space-y-2">
                  <div className="flex justify-between items-center text-[10px] border-b border-slate-250 pb-1.5">
                    <span className="text-slate-500">IMMUNE DEFENSE ACTION</span>
                    <span className={`px-2 py-0.5 rounded font-extrabold ${
                      telemetry.ai_explanation.action === "MONITORING" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"
                    }`}>
                      {telemetry.ai_explanation.action}
                    </span>
                  </div>

                  <ul className="space-y-1 text-slate-600 leading-relaxed text-[10px] pl-3 list-disc">
                    {telemetry.ai_explanation.reason.map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                  
                  <div className="flex justify-between text-[9px] text-slate-500 pt-1">
                    <span>Core Confidence:</span>
                    <span className="text-cyan-600 font-bold">{telemetry.ai_explanation.confidence}%</span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-100 pt-3 text-[10px] font-mono text-slate-500 space-y-1">
                <div className="flex justify-between">
                  <span>Model snapshot hash:</span>
                  <span className="text-slate-600 font-semibold">{telemetry.active_model_hash.slice(0, 20)}...</span>
                </div>
                <div className="flex justify-between">
                  <span>Adversarial Shielding:</span>
                  <span className={telemetry.learning_frozen ? "text-orange-600 animate-pulse font-bold" : "text-emerald-600"}>
                    {telemetry.learning_frozen ? "FREEZE STATE (ACTIVE RECOVERY)" : "SHIELD ENFORCED"}
                  </span>
                </div>
              </div>
            </section>
          </div>

          {/* HOST BACKGROUND SECURITY MONITOR */}
          <section className="border border-slate-200 bg-white rounded p-5 shadow-md font-mono text-xs mt-6">
            <h3 className="text-xs font-bold text-slate-700 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2">
              <Activity className="w-4 h-4 text-cyan-600" /> Host Background Security Monitor
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Host CPU & Memory */}
              <div className="space-y-3">
                <div className="flex justify-between font-bold text-slate-500 uppercase text-[10px]">
                  <span>Host Performance</span>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] ${telemetry.host_monitor.device_health > 80 ? "bg-emerald-55 border border-emerald-300 text-emerald-700" : "bg-red-55 border border-red-300 text-red-700"}`}>
                    HEALTH: {telemetry.host_monitor.device_health}%
                  </span>
                </div>
                
                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span>CPU LOAD</span>
                    <span>{telemetry.host_monitor.host_cpu}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded overflow-hidden flex border border-slate-200">
                    <div 
                      className={`h-full ${telemetry.host_monitor.host_cpu > 80 ? "bg-red-500" : "bg-cyan-500"}`}
                      style={{ width: `${telemetry.host_monitor.host_cpu}%` }} 
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span>MEMORY LOAD</span>
                    <span>{telemetry.host_monitor.host_memory}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded overflow-hidden flex border border-slate-200">
                    <div 
                      className={`h-full ${telemetry.host_monitor.host_memory > 80 ? "bg-red-500" : "bg-cyan-500"}`}
                      style={{ width: `${telemetry.host_monitor.host_memory}%` }} 
                    />
                  </div>
                </div>
              </div>

              {/* Host Network */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-500 uppercase text-[10px] pb-1 border-b border-slate-100">Network Sockets</h4>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="bg-slate-50 p-2 rounded border border-slate-100 text-center">
                    <span className="text-[10px] text-slate-400 block uppercase font-bold">Sockets</span>
                    <span className="text-sm font-bold text-slate-700">{telemetry.host_monitor.total_connections}</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded border border-slate-100 text-center">
                    <span className="text-[10px] text-slate-400 block uppercase font-bold">Outbound</span>
                    <span className={`text-sm font-bold ${telemetry.host_monitor.outbound_connections > 5 ? "text-orange-600 font-extrabold animate-pulse" : "text-emerald-600"}`}>
                      {telemetry.host_monitor.outbound_connections}
                    </span>
                  </div>
                </div>
                <div className="text-[9px] text-slate-405 leading-normal">
                  Monitoring outbound TCP connections and active listening ports in real time.
                </div>
              </div>

              {/* Filesystem modifications */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-500 uppercase text-[10px] pb-1 border-b border-slate-100">Folder integrity (Protected)</h4>
                
                {telemetry.host_monitor.file_changes && telemetry.host_monitor.file_changes.length > 0 ? (
                  <div className="bg-red-50 border border-red-200 text-red-700 p-2 rounded text-[10px] space-y-1 max-h-[80px] overflow-y-auto">
                    {telemetry.host_monitor.file_changes.map((change, idx) => (
                      <div key={idx} className="font-bold leading-tight font-mono">{change}</div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-emerald-50 border border-emerald-250 text-emerald-700 p-2.5 rounded text-[10px] text-center">
                    <span className="font-bold block">✓ FILES UNMODIFIED</span>
                    <span className="text-[9px] text-slate-500 block mt-0.5">Integrity check matches local catalog</span>
                  </div>
                )}
              </div>

            </div>

            {/* Running & New processes */}
            <div className="mt-4 pt-3 border-t border-slate-150 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] text-slate-400 block font-bold uppercase mb-1">Active process count: {telemetry.host_monitor.total_processes}</span>
                <span className="text-[9px] text-slate-400 leading-relaxed block">
                  Continuous scan of running background processes to map suspicious binaries.
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-bold uppercase mb-1">New Processes Detected</span>
                <div className="bg-slate-50 border border-slate-200 rounded p-2 text-[10px] max-h-[60px] overflow-y-auto space-y-0.5">
                  {telemetry.host_monitor.new_processes && telemetry.host_monitor.new_processes.length > 0 ? (
                    telemetry.host_monitor.new_processes.map((proc, idx) => (
                      <div key={idx} className="text-orange-600 font-bold">{proc}</div>
                    ))
                  ) : (
                    <div className="text-slate-400 text-center">No new processes spawned since start</div>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* SANDBOX MODULES (LEARNING & PROVENANCE) */}
          <section className="border border-slate-200 bg-white rounded p-5 shadow-md">
            <h3 className="text-xs font-bold text-slate-700 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2 font-mono">
              <Database className="w-4 h-4 text-cyan-600" /> SECURE DATA & LEARNING PIPELINE SANDBOX
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Learning validation */}
              <div className="space-y-3 font-mono">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase">Module 4: Trusted Learning Pipeline API</h4>
                <div className="flex gap-2 items-end">
                  <div className="flex-1">
                    <label htmlFor="sensor-input" className="text-[9px] text-slate-500 block mb-1">PROPOSED SENSOR FLOAT</label>
                    <input
                      id="sensor-input"
                      type="text"
                      value={sensorValInput}
                      onChange={(e) => setSensorValInput(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
                    />
                  </div>
                  <button
                    onClick={handleLearnData}
                    className="py-1.5 px-3 border border-cyan-600 bg-cyan-50 hover:bg-cyan-100 text-xs font-bold text-cyan-700 rounded cursor-pointer transition"
                  >
                    SUBMIT
                  </button>
                </div>

                {learningResult && (
                  <div aria-live="polite" className={`p-2.5 rounded border text-[10px] ${
                    learningResult.status === "ACCEPTED" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"
                  }`}>
                    <div className="font-bold flex items-center gap-1">
                      {learningResult.status === "ACCEPTED" ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      STATUS: {learningResult.status}
                    </div>
                    <p className="text-slate-600 mt-1 leading-normal font-sans">{learningResult.reason}</p>
                  </div>
                )}
              </div>

              {/* Provenance */}
              <div className="space-y-3 font-mono">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase">Module 5: Data Provenance Engine</h4>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label htmlFor="plc-select" className="text-[9px] text-slate-500 block mb-1">REGISTERED SOURCE</label>
                    <select
                      id="plc-select"
                      value={provenanceSource}
                      onChange={(e) => setProvenanceSource(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded p-1 text-[11px] text-slate-800 focus:outline-none"
                    >
                      <option value="OT_SENSOR_PLC_1">OT_SENSOR_PLC_1 (Valid)</option>
                      <option value="OT_SENSOR_PLC_2">OT_SENSOR_PLC_2 (Valid)</option>
                      <option value="UNTRUSTED_INJECTOR_PLC_9">SPOOFED_PLC_9 (Invalid)</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="provenance-hash-input" className="text-[9px] text-slate-500 block mb-1">DATA BLOCK HASH</label>
                    <input
                      id="provenance-hash-input"
                      type="text"
                      value={provenanceHash}
                      onChange={(e) => setProvenanceHash(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded p-1 text-[11px] text-slate-800 focus:outline-none"
                    />
                  </div>
                </div>
                <button
                  onClick={handleValidateData}
                  className="w-full py-1.5 border border-cyan-600 bg-cyan-50 hover:bg-cyan-100 text-xs font-bold text-cyan-700 rounded cursor-pointer transition font-mono"
                >
                  VERIFY CRYPTOGRAPHIC PROVENANCE
                </button>

                {provenanceResult && (
                  <div aria-live="polite" className={`p-2.5 rounded border text-[10px] ${
                    provenanceResult.trusted ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"
                  }`}>
                    <div className="font-bold flex items-center gap-1">
                      {provenanceResult.trusted ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      TRUST: {provenanceResult.trusted ? "PROVEN" : "TAMPERED"}
                    </div>
                    <p className="text-slate-600 mt-1 leading-normal font-sans">{provenanceResult.reason}</p>
                  </div>
                )}
              </div>

            </div>
          </section>

          {/* WEBSOCKET PACKET SNIFFER PANEL */}
          <section className="border border-slate-200 bg-white rounded p-4 shadow font-mono">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2 border-b border-slate-100 pb-1.5">
              <Terminal className="w-3.5 h-3.5 text-cyan-600" /> SECURE WEBSOCKET TELEMETRY LOGS
            </h3>
            <div className="bg-slate-50 border border-slate-200 p-3 rounded h-[120px] overflow-y-auto text-[10px] text-slate-600 space-y-1">
              {wsLogs.map((log, idx) => (
                <div key={idx} className="flex gap-2">
                  <span className="text-slate-400">[{log.time}]</span>
                  <span className={log.dir === "INBOUND" ? "text-cyan-600" : log.dir === "OUTBOUND" ? "text-amber-600" : "text-slate-400"}>
                    {log.dir === "INBOUND" ? "◀" : log.dir === "OUTBOUND" ? "▶" : "•"}
                  </span>
                  <span className="text-slate-700">{log.msg}</span>
                </div>
              ))}
            </div>
          </section>

        </div>

        <div className="w-full lg:w-80 space-y-6">

          {/* TIMELINE LOOP */}
          <section className="border border-slate-200 bg-white rounded p-5 flex flex-col min-h-[350px] shadow-md">
            <h3 className="text-xs font-bold text-slate-700 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2 font-mono">
              <Layers className="w-4 h-4 text-cyan-600" /> EVENT LOG TIMELINE
            </h3>

            <div className="space-y-3 overflow-y-auto max-h-[350px] flex-1 pr-1">
              {[...telemetry.timeline].reverse().map((item, idx) => (
                <div key={idx} className="border border-slate-100 bg-slate-50 p-2.5 rounded font-mono text-[10px]">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-slate-400 font-bold">{item.time}</span>
                    <span className={`uppercase font-extrabold text-[8px] px-1 py-0.5 rounded ${
                      item.severity === "critical" ? "bg-red-50 text-red-700 border border-red-200" :
                      item.severity === "high" ? "bg-orange-50 text-orange-700 border border-orange-200" :
                      "bg-slate-200 text-slate-600 border border-slate-300"
                    }`}>
                      {item.severity}
                    </span>
                  </div>
                  <p className="text-slate-700 leading-relaxed">{item.event}</p>
                </div>
              ))}
            </div>
          </section>

        </div>

      </div>

    </main>
  );
}
