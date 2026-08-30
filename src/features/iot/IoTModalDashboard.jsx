'use client';

import React, { useState, useEffect, useRef } from 'react';

import {
  X,
  Power,
  Cpu,
  Radio,
  Thermometer,
  Droplets,
  Wind,
  Lightbulb,
  Fan,
  Flame,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Send,
  Zap,
  ShieldCheck,
  Smartphone
} from 'lucide-react';

const API_BASE = "http://localhost:8000/api/iot";

const IoTModalDashboard = ({ isOpen, onClose, onSendVoiceCommand }) => {
  const [devices, setDevices] = useState([]);
  const [climate, setClimate] = useState({ temperature: 26.8, humidity: 58.0, motion: "Clear" });
  const [health, setHealth] = useState(null);
  const [schedules, setSchedules] = useState([]);
  const [activeTab, setActiveTab] = useState('devices'); // 'devices', 'sensors', 'schedules', 'health'
  const [loading, setLoading] = useState(false);
  const [commandInput, setCommandInput] = useState('');
  const [actionFeedback, setActionFeedback] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // 1. Fetch initial device list & telemetry
  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [devRes, climRes, schedRes] = await Promise.all([
        fetch(`${API_BASE}/devices`).then(r => r.json()),
        fetch(`${API_BASE}/telemetry`).then(r => r.json()),
        fetch(`${API_BASE}/schedules`).then(r => r.json())
      ]);

      if (devRes.success) setDevices(devRes.devices || []);
      if (climRes.success) setClimate(climRes.climate || {});
      if (schedRes.success) setSchedules(schedRes.schedules || []);
    } catch (err) {
      console.warn("[IoT Dashboard] Fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  // 2. Setup WebSocket for real-time live synchronization
  useEffect(() => {
    if (!isOpen) return;

    fetchAllData();

    try {
      const wsUrl = `ws://${window.location.hostname}:8000/ws/iot`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === "IOT_SNAPSHOT") {
            if (payload.devices) setDevices(payload.devices);
            if (payload.climate) setClimate(payload.climate);
          }
        } catch (e) {}
      };

      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);

      // Polling interval fallback
      const timer = setInterval(fetchAllData, 5000);

      return () => {
        clearInterval(timer);
        if (wsRef.current) wsRef.current.close();
      };
    } catch (e) {
      console.warn("[IoT WS] Error:", e);
    }
  }, [isOpen]);

  // 3. Dispatch Device Command
  const handleDeviceToggle = async (deviceId, currentState) => {
    const nextCmd = currentState === "ON" ? "turn_off" : "turn_on";
    try {
      setActionFeedback({ type: "info", text: `Sending ${nextCmd.replace('_', ' ')}...` });
      const res = await fetch(`${API_BASE}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId, command: nextCmd })
      }).then(r => r.json());

      if (res.success) {
        setActionFeedback({ type: "success", text: res.message || `${deviceId} updated.` });
        fetchAllData();
      } else {
        setActionFeedback({ type: "error", text: res.error || "Execution failed." });
      }
    } catch (err) {
      setActionFeedback({ type: "error", text: "Network connection error." });
    }
    setTimeout(() => setActionFeedback(null), 4000);
  };

  // 4. Submit Natural Language or Text Command
  const handleNaturalSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!commandInput.trim()) return;

    const cmd = commandInput.trim();
    setCommandInput('');
    setActionFeedback({ type: "info", text: `Processing: "${cmd}"...` });

    try {
      const res = await fetch(`${API_BASE}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd })
      }).then(r => r.json());

      if (res.success) {
        setActionFeedback({ type: "success", text: res.message || "Command executed." });
        fetchAllData();
      } else {
        setActionFeedback({ type: "error", text: res.error || "Command failed." });
      }
    } catch (err) {
      setActionFeedback({ type: "error", text: "Command delivery failed." });
    }
    setTimeout(() => setActionFeedback(null), 5000);
  };

  // 5. Run Health Check
  const handleRunHealthCheck = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/health`).then(r => r.json());
      if (res.success) {
        setHealth(res.health);
        setActiveTab('health');
      }
    } catch (e) {
      console.warn("Health check error:", e);
    } finally {
      setLoading(false);
    }
  };

  // Helper Icon Resolver
  const getDeviceIcon = (type) => {
    switch (type) {
      case 'light': return <Lightbulb className="w-5 h-5 text-amber-400" />;
      case 'fan': return <Fan className="w-5 h-5 text-cyan-400" />;
      case 'ac': return <Wind className="w-5 h-5 text-blue-400" />;
      case 'sensor': return <Thermometer className="w-5 h-5 text-emerald-400" />;
      case 'heater': return <Flame className="w-5 h-5 text-rose-500" />;
      case 'esp32': return <Cpu className="w-5 h-5 text-purple-400" />;
      default: return <Radio className="w-5 h-5 text-cyan-400" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in font-sans text-slate-200">
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-slate-950/90 border border-cyan-500/30 rounded-2xl shadow-[0_0_50px_rgba(6,182,212,0.15)] overflow-hidden">
        
        {/* TOP GLOW ACCENT BAR */}
        <div className="h-1 w-full bg-gradient-to-r from-cyan-500 via-purple-500 to-emerald-500 shadow-[0_0_12px_rgba(6,182,212,0.8)]" />

        {/* MODAL HEADER */}
        <div className="flex items-center justify-between px-4 py-3 sm:px-6 sm:py-4 border-b border-white/[0.06] bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold tracking-wider text-white uppercase">
                  ORIAN IoT Control System
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  MOBILE CORE v2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Direct ESP32 Microcontroller & MQTT Neural Gateway
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Beacon */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-white/10 text-[11px] font-mono">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-amber-400'} animate-pulse`} />
              <span className={wsConnected ? 'text-emerald-400' : 'text-amber-400'}>
                {wsConnected ? 'LIVE WS SYNC' : 'POLLING MODE'}
              </span>
            </div>

            <button
              onClick={fetchAllData}
              disabled={loading}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-all hover:scale-105 active:scale-95"
              title="Refresh Devices"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 transition-all hover:scale-105 active:scale-95"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* FEEDBACK BANNER */}
        {actionFeedback && (
          <div className={`px-4 py-2 text-xs font-mono flex items-center gap-2 border-b transition-all ${
            actionFeedback.type === 'error'
              ? 'bg-rose-950/60 border-rose-500/30 text-rose-300'
              : actionFeedback.type === 'success'
              ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300'
              : 'bg-cyan-950/60 border-cyan-500/30 text-cyan-300'
          }`}>
            {actionFeedback.type === 'error' ? <AlertTriangle className="w-4 h-4 shrink-0" /> : <CheckCircle className="w-4 h-4 shrink-0" />}
            <span>{actionFeedback.text}</span>
          </div>
        )}

        {/* NAVIGATION TABS */}
        <div className="flex items-center gap-2 px-4 pt-3 border-b border-white/[0.06] bg-slate-900/30 overflow-x-auto no-scrollbar">
          {[
            { id: 'devices', label: 'Devices', icon: Zap },
            { id: 'sensors', label: 'Sensors & Climate', icon: Activity },
            { id: 'schedules', label: 'Schedules', icon: Clock },
            { id: 'health', label: 'System Health', icon: ShieldCheck }
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  if (tab.id === 'health' && !health) handleRunHealthCheck();
                  setActiveTab(tab.id);
                }}
                className={`flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-t-xl transition-all border-t border-x ${
                  active
                    ? 'bg-slate-950 border-cyan-500/40 text-cyan-300 shadow-[0_-2px_10px_rgba(6,182,212,0.15)] font-bold'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* TAB CONTENT AREA */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 max-h-[60vh]">
          
          {/* TAB 1: HARDWARE DEVICES GRID */}
          {activeTab === 'devices' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {devices.map(device => {
                  const isOnline = device.status === 'ONLINE';
                  const isOn = device.state === 'ON';
                  const isCritical = device.is_safety_critical;

                  return (
                    <div
                      key={device.device_id}
                      className={`relative flex flex-col justify-between p-4 rounded-xl border transition-all duration-300 ${
                        isOn
                          ? 'bg-cyan-950/20 border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.12)]'
                          : 'bg-slate-900/40 border-white/[0.07] hover:border-white/20'
                      }`}
                    >
                      {/* Card Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`p-2.5 rounded-xl border ${
                            isOn ? 'bg-cyan-500/20 border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.3)]' : 'bg-slate-800/80 border-white/10'
                          }`}>
                            {getDeviceIcon(device.device_type)}
                          </div>
                          <div>
                            <h3 className="text-sm font-semibold text-white tracking-wide">
                              {device.device_name}
                            </h3>
                            <span className="text-[10px] font-mono text-slate-400">
                              {device.location} • {device.device_id}
                            </span>
                          </div>
                        </div>

                        {/* Status Pill */}
                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/40 border border-white/10 text-[9px] font-mono">
                          <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-rose-500'}`} />
                          <span className={isOnline ? 'text-emerald-400' : 'text-rose-400'}>
                            {device.status}
                          </span>
                        </div>
                      </div>

                      {/* Card Footer / Toggle Controls */}
                      <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between">
                        <div className="text-[11px] font-mono">
                          <span className="text-slate-400">STATE: </span>
                          <span className={`font-bold ${isOn ? 'text-cyan-400' : 'text-slate-500'}`}>
                            {device.state}
                          </span>
                        </div>

                        {device.device_type !== 'sensor' && (
                          <button
                            onClick={() => handleDeviceToggle(device.device_id, device.state)}
                            disabled={!isOnline}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                              !isOnline
                                ? 'bg-slate-800 text-slate-600 cursor-not-allowed border border-white/5'
                                : isOn
                                ? 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/10'
                            }`}
                          >
                            <Power className="w-3.5 h-3.5" />
                            <span>{isOn ? 'TURN OFF' : 'TURN ON'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Quick Preset Actions Bar */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/[0.06] flex flex-wrap items-center justify-between gap-3">
                <span className="text-xs text-slate-400 font-mono">
                  QUICK PRESETS:
                </span>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleNaturalSubmit({ preventDefault: () => {}, target: {} }, "turn off all")}
                    className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-mono transition-all"
                  >
                    Turn Everything Off
                  </button>
                  <button
                    onClick={() => handleNaturalSubmit({ preventDefault: () => {}, target: {} }, "turn on all")}
                    className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-mono transition-all"
                  >
                    Turn Everything On
                  </button>
                  <button
                    onClick={handleRunHealthCheck}
                    className="px-3 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs font-mono transition-all"
                  >
                    Check IoT System
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SENSORS & CLIMATE GAUGES */}
          {activeTab === 'sensors' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Temperature Card */}
                <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-500/10 via-slate-900/50 to-slate-950 border border-amber-500/30 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 text-amber-400 mb-1">
                      <Thermometer className="w-5 h-5" />
                      <span className="text-xs font-mono uppercase tracking-wider">Room Temperature</span>
                    </div>
                    <div className="text-3xl sm:text-4xl font-black text-white font-mono">
                      {climate.temperature}°C
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1 font-mono">
                      Optimal Range: 22°C - 28°C
                    </p>
                  </div>
                  <div className="w-16 h-16 rounded-full border-4 border-amber-500/40 flex items-center justify-center text-amber-400 font-bold text-sm bg-amber-500/10">
                    DHT22
                  </div>
                </div>

                {/* Humidity Card */}
                <div className="p-5 rounded-2xl bg-gradient-to-br from-cyan-500/10 via-slate-900/50 to-slate-950 border border-cyan-500/30 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 text-cyan-400 mb-1">
                      <Droplets className="w-5 h-5" />
                      <span className="text-xs font-mono uppercase tracking-wider">Relative Humidity</span>
                    </div>
                    <div className="text-3xl sm:text-4xl font-black text-white font-mono">
                      {climate.humidity}%
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1 font-mono">
                      Target Comfort: 50% - 65%
                    </p>
                  </div>
                  <div className="w-16 h-16 rounded-full border-4 border-cyan-500/40 flex items-center justify-center text-cyan-400 font-bold text-sm bg-cyan-500/10">
                    REAL
                  </div>
                </div>
              </div>

              {/* Climate Telemetry Details */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/[0.06] font-mono text-xs space-y-2">
                <div className="flex justify-between border-b border-white/[0.04] pb-1.5">
                  <span className="text-slate-400">Motion Detection Status:</span>
                  <span className="text-emerald-400 font-bold">{climate.motion || 'Clear'}</span>
                </div>
                <div className="flex justify-between border-b border-white/[0.04] pb-1.5">
                  <span className="text-slate-400">Air Quality Index:</span>
                  <span className="text-cyan-400 font-bold">Good (38 AQI)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Sensor Telemetry Refresh Rate:</span>
                  <span className="text-slate-300">10 Seconds (ESP32 Stream)</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: SCHEDULES */}
          {activeTab === 'schedules' && (
            <div className="space-y-3">
              {schedules.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-white/10 rounded-xl">
                  <Clock className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                  <p className="text-sm text-slate-400">No active automated IoT schedules.</p>
                  <p className="text-xs text-slate-500 font-mono mt-1">
                    Try voice commands like: "Turn off room light in 15 minutes"
                  </p>
                </div>
              ) : (
                schedules.map(s => (
                  <div key={s.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-white/[0.08] flex items-center justify-between font-mono text-xs">
                    <div>
                      <span className="font-bold text-cyan-300">{s.command.replace('_', ' ').toUpperCase()}</span> on <span className="text-white">{s.device_id}</span>
                      <div className="text-[10px] text-slate-400">
                        Scheduled for: {new Date(s.scheduled_time * 1000).toLocaleTimeString()} ({s.recurrence})
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px]">
                      {s.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 4: SYSTEM HEALTH & DIAGNOSTICS */}
          {activeTab === 'health' && (
            <div className="space-y-4">
              {health ? (
                <>
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/30 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-mono text-slate-400">OVERALL SYSTEM HEALTH SCORE</span>
                      <div className="text-3xl font-black text-cyan-400 font-mono">
                        {health.health_score}%
                      </div>
                    </div>
                    <div className="text-right text-xs font-mono text-slate-300">
                      <div>Database: <span className="text-emerald-400">{health.database_status}</span></div>
                      <div>Communication: <span className="text-cyan-400">{health.mqtt_broker_status}</span></div>
                      <div>Online Devices: <span className="text-emerald-400">{health.devices_online}/{health.devices_total}</span></div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xs font-mono font-bold text-slate-300 uppercase">Diagnostic Checks</h4>
                    {health.checks?.map((c, i) => (
                      <div key={i} className="p-3 rounded-lg bg-slate-900/50 border border-white/[0.04] flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-300">{c.component}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-slate-400">{c.message}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            c.status === 'PASSED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                          }`}>
                            {c.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="p-6 text-center">
                  <button
                    onClick={handleRunHealthCheck}
                    className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs font-mono"
                  >
                    Run Full IoT Health Diagnostics
                  </button>
                </div>
              )}
            </div>
          )}

        </div>

        {/* NATURAL LANGUAGE / VOICE COMMAND BAR */}
        <div className="p-3 sm:p-4 border-t border-white/[0.06] bg-slate-900/80">
          <form onSubmit={handleNaturalSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder='e.g. "Turn on room light", "What is the temperature?", "Turn off fan in 10 mins"...'
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-slate-600"
            />
            <button
              type="submit"
              disabled={!commandInput.trim()}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-mono font-bold text-xs flex items-center gap-1.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(6,182,212,0.3)]"
            >
              <Send className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">DISPATCH</span>
            </button>
          </form>
        </div>

      </div>
    </div>
  );
};

export default IoTModalDashboard;
