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
  Fingerprint,
  Battery,
  HardDrive
} from "lucide-react";

export default function App() {
  const [wsStatus, setWsStatus] = useState("DISCONNECTED");
  const [telemetry, setTelemetry] = useState({
    status: "SAFE",
    risk_level: "LOW",
    risk_value: 12,
    cpu_usage: 12.0,
    ram_usage: 45.5,
    battery_level: 95,
    active_processes: [],
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
    active_sessions: []
  });

  const [cmdError, setCmdError] = useState("");
  const [wsLogs, setWsLogs] = useState([]);
  const [showPhoneMock, setShowPhoneMock] = useState(true);

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
    addWsLog("SYSTEM", "Initiating encrypted WebSocket handshake with Sentinel Agent...");
    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus("CONNECTED");
      addWsLog("SYSTEM", "Sentinel Secure Channel ESTABLISHED (AES-GCM)");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        addWsLog("INBOUND", `Event: ${payload.type}`);
        if (payload.type === "TELEMETRY") {
          setTelemetry(payload.data);
        }
      } catch (err) {
        console.error("WS parse error", err);
      }
    };

    ws.onclose = () => {
      setWsStatus("DISCONNECTED");
      addWsLog("SYSTEM", "Agent disconnected. Retrying...");
      setTimeout(connectWS, 3000);
    };
  };

  const triggerAction = async (actionType, payload = {}) => {
    if (telemetry.workstation_blocked) {
      setCmdError("SENTINEL BLOCK: Lockout active. Mobile Guardian signature required.");
      addWsLog("OUTBOUND", `BLOCKED CMD: ${actionType}`);
      return;
    }
    setCmdError("");
    addWsLog("OUTBOUND", `EXEC CMD: ${actionType}`);
    try {
      const res = await fetch("http://localhost:8000/api/laptop/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: actionType, payload })
      });
      const data = await res.json();
      if (res.status === 403) {
        setCmdError(data.detail);
      }
    } catch (e) {
      setCmdError("API connection failure.");
    }
  };

  const triggerAttackScenario = async (type) => {
    addWsLog("SYSTEM", `Simulating Intrusion Alert: ${type}`);
    try {
      await fetch("http://localhost:8000/api/simulate-attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type })
      });
    } catch (e) {
      console.error(e);
    }
  };

  const submitGuardianDecision = async (decision) => {
    addWsLog("SYSTEM", `Sending Mobile Trust Signature: ${decision}`);
    try {
      await fetch("http://localhost:8000/api/respond-emergency", {
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
      await fetch("http://localhost:8000/api/reset", { method: "POST" });
      setCmdError("");
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <main className="min-h-screen bg-[#07080c] p-4 md:p-6 text-slate-200 relative font-mono selection:bg-cyan-500 selection:text-black">
      
      {/* GLOW TOP SHIELD */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent shadow-[0_0_15px_rgba(0,212,255,0.8)]" />

      {/* HEADER */}
      <header className="border border-cyan-500/20 bg-[#0d0e15] p-4 flex flex-wrap justify-between items-center mb-6 rounded shadow-[0_0_20px_rgba(0,212,255,0.05)] relative overflow-hidden">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-950/40 rounded border border-cyan-500/30">
            <Shield className="w-8 h-8 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-widest text-white uppercase">
              Omega Sentinel Client Agent
            </h1>
            <p className="text-[10px] text-cyan-400/70 tracking-widest uppercase">
              Laptop Secure Remote Management & Intrusion Guard
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-3 lg:mt-0 flex-wrap">
          <div className="flex items-center gap-2 border border-cyan-500/30 px-3 py-1.5 rounded bg-cyan-950/20 text-[10px] text-cyan-400">
            {wsStatus === "CONNECTED" ? (
              <>
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                <span>AGENT ONLINE</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-red-500">DISCONNECTED</span>
              </>
            )}
          </div>

          <button
            onClick={resetState}
            className="flex items-center gap-1.5 border border-cyan-500/30 hover:border-cyan-400/80 bg-[#11131c] px-3 py-1.5 rounded text-[11px] hover:bg-cyan-950/20 transition cursor-pointer text-cyan-400"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            RESET SYSTEM
          </button>

          <button
            onClick={() => setShowPhoneMock(!showPhoneMock)}
            className={`flex items-center gap-1.5 border px-3 py-1.5 rounded text-[11px] transition cursor-pointer ${
              showPhoneMock ? "border-cyan-500 bg-cyan-950/40 text-cyan-300" : "border-cyan-500/30 bg-[#11131c] text-slate-400"
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            {showPhoneMock ? "HIDE TRUSTED MOBILE" : "SHOW TRUSTED MOBILE"}
          </button>
        </div>
      </header>

      {/* DYNAMIC SCENARIO PANEL */}
      <section className="border border-cyan-500/10 bg-[#0d0e15] p-4 rounded mb-6">
        <div className="flex items-center justify-between border-b border-cyan-500/10 pb-2 mb-3">
          <h2 className="text-xs font-bold text-cyan-300 tracking-widest uppercase flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" /> Attack Vector Simulation Console
          </h2>
          <span className="text-[9px] text-slate-500">TRIGGER LOCAL INTENT THREATS</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => triggerAttackScenario("WEIGHT_TAMPER")}
            className={`py-2 px-3 border rounded text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "WEIGHT_TAMPER" ? "border-red-500 bg-red-950/20 text-red-400" : "border-cyan-500/20 bg-[#11131c] text-slate-300 hover:border-cyan-500/50"
            }`}
          >
            <div className="font-bold">1. File Tampering Anomaly</div>
            <div className="text-[9px] text-slate-500 mt-0.5">Integrity hash checks fail</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("PLC_SPOOF")}
            className={`py-2 px-3 border rounded text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "PLC_SPOOF" ? "border-red-500 bg-red-950/20 text-red-400" : "border-cyan-500/20 bg-[#11131c] text-slate-300 hover:border-cyan-500/50"
            }`}
          >
            <div className="font-bold">2. Rogue Process Executed</div>
            <div className="text-[9px] text-slate-500 mt-0.5">Suspicious task executing in background</div>
          </button>

          <button
            onClick={() => triggerAttackScenario("TOKEN_STEAL")}
            className={`py-2 px-3 border rounded text-xs text-left transition cursor-pointer ${
              telemetry.compromise_type === "TOKEN_STEAL" ? "border-red-500 bg-red-950/20 text-red-400" : "border-cyan-500/20 bg-[#11131c] text-slate-300 hover:border-cyan-500/50"
            }`}
          >
            <div className="font-bold">3. Session Key Hijacking</div>
            <div className="text-[9px] text-slate-500 mt-0.5">Stolen login keys used remotely</div>
          </button>

          <button
            onClick={() => triggerAction("SHUTDOWN")}
            className="py-2 px-3 border border-red-500/30 bg-red-950/20 hover:bg-red-900/20 text-red-400 rounded text-xs text-left transition cursor-pointer"
          >
            <div className="font-bold">4. Lock Station Remotely</div>
            <div className="text-[9px] text-red-400/60 mt-0.5">Simulate critical lockdown trigger</div>
          </button>
        </div>
      </section>

      {/* CORE DISPLAY (GRID) */}
      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* SCADA WORKSTATION */}
        <div className="flex-1 space-y-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* LAPTOP AGENT TELEMETRY */}
            <section className="border border-cyan-500/20 bg-[#0d0e15] rounded p-5 relative overflow-hidden flex flex-col justify-between min-h-[360px]">
              {telemetry.workstation_blocked && (
                <div className="absolute inset-0 bg-[#1c0707]/90 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center p-4 text-center">
                  <Lock className="w-12 h-12 text-red-500 mb-2 animate-bounce" />
                  <span className="text-xs font-bold text-red-500 tracking-wider">
                    SENTINEL AGENT LOCKDOWN ACTIVE
                  </span>
                  <span className="text-[10px] text-slate-400 mt-1 max-w-[200px]">
                    Authority transferred to Mobile Guardian
                  </span>
                </div>
              )}

              <div>
                <h3 className="text-xs font-bold text-cyan-400 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-cyan-500/10 pb-2">
                  <Activity className="w-4 h-4 text-cyan-400" /> Laptop Health & Telemetry
                </h3>

                <div className="grid grid-cols-2 gap-4 my-6 text-center">
                  <div className="border border-cyan-500/10 rounded p-3 bg-cyan-950/10">
                    <Cpu className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                    <span className="text-[9px] text-slate-500 block">CPU LOAD</span>
                    <span className="text-lg font-bold text-white">{telemetry.cpu_usage}%</span>
                  </div>
                  
                  <div className="border border-cyan-500/10 rounded p-3 bg-cyan-950/10">
                    <HardDrive className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                    <span className="text-[9px] text-slate-500 block">RAM USAGE</span>
                    <span className="text-lg font-bold text-white">{telemetry.ram_usage}%</span>
                  </div>
                  
                  <div className="border border-cyan-500/10 rounded p-3 bg-cyan-950/10 col-span-2">
                    <Battery className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                    <span className="text-[9px] text-slate-500 block">BATTERY CHARGE</span>
                    <span className="text-lg font-bold text-white">{telemetry.battery_level}%</span>
                  </div>
                </div>
              </div>

              {/* Console operations */}
              <div className="border-t border-cyan-500/10 pt-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => triggerAction("LOCK")}
                    className="flex-1 py-2 px-3 border border-cyan-500/30 bg-[#11131c] hover:bg-cyan-950/20 text-cyan-400 text-[10px] font-bold cursor-pointer transition rounded"
                  >
                    LOCK LAPTOP
                  </button>
                  <button
                    onClick={() => triggerAction("MUTE")}
                    className="flex-1 py-2 px-3 border border-cyan-500/30 bg-[#11131c] hover:bg-cyan-950/20 text-cyan-400 text-[10px] font-bold cursor-pointer transition rounded"
                  >
                    TOGGLE MUTE
                  </button>
                </div>
                
                {cmdError && (
                  <p className="mt-3 text-red-500 text-[10px] leading-tight border border-red-500/30 p-2 rounded bg-red-950/10">
                    {cmdError}
                  </p>
                )}
              </div>
            </section>

            {/* CYBER RISK / AI EXPLAINABLE CORE */}
            <section className="border border-cyan-500/20 bg-[#0d0e15] rounded p-5 flex flex-col justify-between min-h-[360px]">
              <div>
                <h3 className="text-xs font-bold text-cyan-400 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-cyan-500/10 pb-2">
                  <Cpu className="w-4 h-4 text-cyan-400" /> RISK & XAI TRUST ENGINE
                </h3>

                <div className="mb-4">
                  <div className="flex justify-between text-[10px] mb-1 text-slate-400">
                    <span>AGENT RISK EVALUATION</span>
                    <span>{telemetry.risk_value}%</span>
                  </div>
                  <div className="h-3.5 bg-slate-900 rounded overflow-hidden flex p-[2px] border border-cyan-500/20">
                    <div 
                      className={`h-full rounded-sm transition-all duration-500 ${
                        telemetry.risk_level === "LOW" ? "bg-emerald-500" :
                        telemetry.risk_level === "MEDIUM" ? "bg-yellow-500" :
                        telemetry.risk_level === "HIGH" ? "bg-orange-500" :
                        "bg-red-500"
                      }`} 
                      style={{ width: `${telemetry.risk_value}%` }} 
                    />
                  </div>
                </div>

                {/* XAI */}
                <div className="bg-[#11131c] border border-cyan-500/10 p-3 rounded text-[11px] space-y-2">
                  <div className="flex justify-between items-center text-[10px] border-b border-cyan-500/10 pb-1.5">
                    <span className="text-slate-500">IMMUNE DEFENSE ACTION</span>
                    <span className={`px-2 py-0.5 rounded font-extrabold ${
                      telemetry.ai_explanation.action === "MONITORING" ? "bg-emerald-950/20 text-emerald-400" : "bg-red-950/20 text-red-400"
                    }`}>
                      {telemetry.ai_explanation.action}
                    </span>
                  </div>

                  <ul className="space-y-1 text-slate-400 leading-relaxed text-[10px] pl-3 list-disc">
                    {telemetry.ai_explanation.reason.map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                  
                  <div className="flex justify-between text-[9px] text-slate-500 pt-1">
                    <span>Core Confidence:</span>
                    <span className="text-cyan-400 font-bold">{telemetry.ai_explanation.confidence}%</span>
                  </div>
                </div>
              </div>

              <div className="border-t border-cyan-500/10 pt-3 text-[10px] text-slate-500 space-y-1">
                <div className="flex justify-between">
                  <span>Registered Device Binding:</span>
                  <span className="text-cyan-400 font-semibold">SHA256_FINGERPRINT_3a9c7</span>
                </div>
                <div className="flex justify-between">
                  <span>Adversarial Shielding:</span>
                  <span className={telemetry.learning_frozen ? "text-orange-500 animate-pulse font-bold" : "text-emerald-500"}>
                    {telemetry.learning_frozen ? "FREEZE STATE (ACTIVE RECOVERY)" : "SHIELD ENFORCED"}
                  </span>
                </div>
              </div>
            </section>
          </div>

          {/* PROCESS MANAGER AND ACTIVE SESSIONS */}
          <section className="border border-cyan-500/20 bg-[#0d0e15] rounded p-5">
            <h3 className="text-xs font-bold text-cyan-400 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-cyan-500/10 pb-2">
              <Database className="w-4 h-4 text-cyan-400" /> Active System Processes & Sessions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Processes list */}
              <div className="space-y-3">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase">Top CPU Processes</h4>
                <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
                  {telemetry.active_processes.map((proc, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs border border-cyan-500/10 p-2 rounded bg-cyan-950/5">
                      <div>
                        <span className="text-white font-bold">{proc.name}</span>
                        <span className="text-slate-500 text-[9px] block">PID: {proc.pid}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-cyan-400 font-bold">{proc.cpu}%</span>
                        <button 
                          onClick={() => triggerAction("KILL_PROCESS", { pid: proc.pid })}
                          className="px-2 py-0.5 bg-red-950/20 border border-red-500/30 hover:border-red-500 text-red-400 rounded text-[9px]"
                        >
                          KILL
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sessions list */}
              <div className="space-y-3">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase">Active Sessions</h4>
                <div className="space-y-2 max-h-[160px] overflow-y-auto">
                  {telemetry.active_sessions.map((sess, idx) => (
                    <div key={idx} className="text-xs border border-cyan-500/10 p-2 rounded bg-cyan-950/5 flex justify-between items-center">
                      <div>
                        <span className="text-white font-bold">User: {sess.user}</span>
                        <span className="text-slate-500 text-[9px] block">IP: {sess.ip} | Device: {sess.device}</span>
                      </div>
                      <button 
                        onClick={() => triggerAction("MUTE")}
                        className="px-2 py-0.5 bg-red-950/20 border border-red-500/30 text-red-400 rounded text-[9px] hover:border-red-500"
                      >
                        REVOKE
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </section>

          {/* WEBSOCKET PACKET SNIFFER PANEL */}
          <section className="border border-cyan-500/20 bg-[#0d0e15] rounded p-4">
            <h3 className="text-xs font-bold text-cyan-400 tracking-widest mb-3 flex items-center gap-2 border-b border-cyan-500/10 pb-1.5">
              <Terminal className="w-3.5 h-3.5 text-cyan-400" /> Secure Agent Socket Logs
            </h3>
            <div className="bg-slate-950/50 border border-cyan-500/10 p-3 rounded h-[120px] overflow-y-auto text-[10px] text-slate-400 space-y-1">
              {wsLogs.map((log, idx) => (
                <div key={idx} className="flex gap-2">
                  <span className="text-slate-650">[{log.time}]</span>
                  <span className={log.dir === "INBOUND" ? "text-cyan-400" : log.dir === "OUTBOUND" ? "text-amber-500" : "text-slate-500"}>
                    {log.dir === "INBOUND" ? "◀" : log.dir === "OUTBOUND" ? "▶" : "•"}
                  </span>
                  <span className="text-slate-300">{log.msg}</span>
                </div>
              ))}
            </div>
          </section>

        </div>

        {/* VIRTUAL MOBILE GUARDIAN OR TIMELINE SIDEBAR */}
        <div className="w-full lg:w-80 space-y-6">
          
          {/* VIRTUAL PHONE EMULATOR */}
          {showPhoneMock && (
            <section className="border-4 border-slate-700 bg-black rounded-[30px] p-4 min-h-[480px] shadow-xl relative flex flex-col justify-between overflow-hidden">
              {/* Speaker / Notch */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-5 bg-slate-800 rounded-b-xl z-20 flex items-center justify-center">
                <span className="w-10 h-1 bg-slate-900 rounded-full" />
              </div>

              {/* Lock screen / Alert */}
              <div className="flex-1 flex flex-col justify-between pt-6">
                <div className="text-center pb-2 border-b border-cyan-500/10 mt-1">
                  <span className="text-[9px] text-cyan-400 tracking-widest font-bold">OMEGA GUARD MOBILE LINK</span>
                </div>

                {telemetry.emergency_active ? (
                  <div className="my-auto space-y-4 px-2 py-4 bg-red-950/20 border border-red-500/30 rounded-2xl flex flex-col items-center text-center">
                    <Fingerprint className="w-12 h-12 text-red-500 animate-pulse" />
                    
                    <div>
                      <h4 className="text-red-400 font-extrabold text-xs tracking-wider">
                        🚨 ACTION REQUIRES APPROVAL
                      </h4>
                      <p className="text-[10px] text-slate-300 mt-2 leading-relaxed">
                        Command: <span className="text-white underline">{telemetry.pending_emergency_command || "Lock Workstation"}</span>
                      </p>
                      <p className="text-[9px] text-slate-500 mt-1.5">
                        Alert: {telemetry.compromise_type}
                      </p>
                    </div>

                    <div className="flex gap-2 w-full pt-2">
                      <button
                        onClick={() => submitGuardianDecision("APPROVE")}
                        className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-[10px] rounded-lg cursor-pointer transition shadow"
                      >
                        APPROVE
                      </button>
                      <button
                        onClick={() => submitGuardianDecision("REJECT")}
                        className="flex-1 py-2 bg-red-600 hover:bg-red-500 text-white font-extrabold text-[10px] rounded-lg cursor-pointer transition shadow"
                      >
                        REJECT
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="my-auto flex flex-col items-center justify-center p-6 text-center text-slate-500">
                    <Smartphone className="w-12 h-12 mb-3 text-slate-700" />
                    <p className="text-[10px] leading-relaxed">
                      Encrypted connection active. Awaiting validation requests from Laptop Agent.
                    </p>
                  </div>
                )}

                {/* Secure Bound device status */}
                <div className="pt-3 border-t border-cyan-500/10 text-center">
                  <span className="text-[9px] text-slate-500 block">DEVICE BINDING ID</span>
                  <span className="text-[10px] text-cyan-400 font-bold">SHA256_FINGERPRINT_3a9c7</span>
                </div>
              </div>

              {/* Bottom bar indicator */}
              <div className="w-32 h-1 bg-slate-800 mx-auto mt-4 rounded-full" />
            </section>
          )}

          {/* TIMELINE */}
          <section className="border border-cyan-500/20 bg-[#0d0e15] rounded p-5 flex flex-col min-h-[350px]">
            <h3 className="text-xs font-bold text-cyan-400 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-cyan-500/10 pb-2">
              <Layers className="w-4 h-4 text-cyan-400" /> SECURITY EVENTS TIMELINE
            </h3>

            <div className="space-y-3 overflow-y-auto max-h-[350px] flex-1 pr-1">
              {[...telemetry.timeline].reverse().map((item, idx) => (
                <div key={idx} className="border border-cyan-500/10 bg-[#11131c] p-2.5 rounded text-[10px]">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-slate-500 font-bold">{item.time}</span>
                    <span className={`uppercase font-extrabold text-[8px] px-1 py-0.5 rounded ${
                      item.severity === "critical" ? "bg-red-950/20 text-red-400 border border-red-500/30" :
                      item.severity === "high" ? "bg-orange-950/20 text-orange-400 border border-orange-500/30" :
                      "bg-cyan-950/20 text-cyan-400 border border-cyan-500/30"
                    }`}>
                      {item.severity}
                    </span>
                  </div>
                  <p className="text-slate-350 leading-relaxed">{item.event}</p>
                </div>
              ))}
            </div>
          </section>

        </div>

      </div>

    </main>
  );
}
