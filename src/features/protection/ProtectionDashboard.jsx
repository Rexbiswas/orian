'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';

import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, ShieldAlert, Laptop, Smartphone, Power, 
  Activity, Bell, RefreshCw, Filter, Settings, Play, 
  CheckCircle, Plus, Eye, Lock, Sliders, AlertCircle
} from 'lucide-react';
import { API_BASE_URL, WS_BASE_URL } from '../../config';
import MobileAlertCard from './MobileAlertCard';
import AlertDetailsModal from './AlertDetailsModal';
import MobileDeviceManager from './MobileDeviceManager';
import { playSuccessChime, playHoverClick } from '../../utils/sound';

const ProtectionDashboard = ({ isOpen, onClose }) => {
  const [data, setData] = useState({
    protection_enabled: true,
    automatic_sleep_enabled: true,
    focus_mode: { is_active: false, mode: 'WORK' },
    metrics: {
      warnings_today: 0,
      violations_today: 0,
      security_events_today: 0,
      overrides_today: 0,
      sleep_actions_today: 0
    },
    recent_alerts: [],
    mobile_devices: [],
    active_devices_count: 1
  });

  const [loading, setLoading] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [activeTab, setActiveTab] = useState('alerts'); // alerts, devices, policies
  const [alertFilter, setAlertFilter] = useState('ALL'); // ALL, SECURITY, PRODUCTIVITY, UNREAD
  const [isTestTriggering, setIsTestTriggering] = useState(false);
  const wsRef = useRef(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/protection/dashboard`);
      if (res.data.success) {
        setData(res.data);
      }
    } catch (err) {
      console.error("Dashboard fetch fault:", err);
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    fetchDashboardData();

    // WebSocket real-time subscription
    const wsUrl = `${WS_BASE_URL || API_BASE_URL.replace('http', 'ws')}/ws/protection`;
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          if (payload.type === 'MOBILE_ALERT_PUSH' || payload.event === 'PROTECTION_SNAPSHOT' || payload.type === 'ORIAN_PROTECTION_ALERT') {
            fetchDashboardData();
          }
        } catch (e) {
          console.debug("WS payload parse error", e);
        }
      };

      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    } catch (err) {
      console.error("Protection WS fault:", err);
    }
  }, [isOpen, fetchDashboardData]);

  const handleAcknowledge = async (eventId) => {
    try {
      const token = localStorage.getItem('orian_token') || '';
      await axios.post(`${API_BASE_URL}/api/notifications/${eventId}/acknowledge`, {}, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      playSuccessChime();
      fetchDashboardData();
    } catch (err) {
      console.error("Acknowledge error:", err);
    }
  };

  const handleExecuteAction = async (payload) => {
    const token = localStorage.getItem('orian_token') || '';
    const res = await axios.post(`${API_BASE_URL}/api/notifications/action`, payload, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    fetchDashboardData();
    return res.data;
  };

  const handleTriggerTestAlert = async (type = 'PRODUCTIVITY_WARNING') => {
    setIsTestTriggering(true);
    try {
      await axios.post(`${API_BASE_URL}/api/notifications/test`, {
        type: type,
        activity: type.includes('SECURITY') ? 'Attempt to disable agent' : 'Gaming detected (Steam)',
        risk: type.includes('SECURITY') ? 'CRITICAL' : 'MEDIUM',
        reason: type.includes('SECURITY') ? 'Tampering detection signal' : 'Focus Mode is active (Work Hours)',
        action: type.includes('SECURITY') ? 'Blocked' : 'Warning issued'
      });
      playSuccessChime();
      fetchDashboardData();
    } catch (err) {
      console.error("Test alert error:", err);
    } finally {
      setIsTestTriggering(false);
    }
  };

  const handleToggleProtection = async () => {
    try {
      const token = localStorage.getItem('orian_token') || '';
      await axios.post(`${API_BASE_URL}/api/protection/emergency-disable`, {
        disable_all_protection: data.protection_enabled,
        owner_verification: 'owner-toggle'
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      playSuccessChime();
      fetchDashboardData();
    } catch (err) {
      console.error("Toggle error:", err);
    }
  };

  if (!isOpen) return null;

  const filteredAlerts = (data.recent_alerts || []).filter((a) => {
    if (alertFilter === 'UNREAD') return a.status !== 'ACKNOWLEDGED';
    if (alertFilter === 'SECURITY') return a.type?.includes('SECURITY') || a.type?.includes('MALWARE') || a.type?.includes('TAMPERING');
    if (alertFilter === 'PRODUCTIVITY') return a.type?.includes('PRODUCTIVITY') || a.type?.includes('BLOCKED') || a.type?.includes('FOCUS');
    return true;
  });

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-xl font-mono">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl bg-[#020611] border border-cyan-500/30 shadow-[0_0_60px_rgba(0,229,255,0.18)] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 sm:p-5 border-b border-white/[0.08] bg-white/[0.02]">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 shadow-[0_0_20px_rgba(0,229,255,0.25)]">
                <ShieldCheck className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm sm:text-base font-bold tracking-widest uppercase text-white font-mono">
                    ORIAN PROTECTION & MOBILE ALERTS
                  </h2>
                  <span className="px-2 py-0.5 rounded text-[8px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    LIVE
                  </span>
                </div>
                <p className="text-[10px] text-white/50">
                  Real-Time Windows Protection, Zero-Surveillance Monitor & Push Alert Gateway
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={fetchDashboardData}
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-colors"
                title="Refresh Status"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white text-xs font-bold transition-colors"
              >
                ESC
              </button>
            </div>
          </div>

          {/* Navigation Sub-Tabs */}
          <div className="flex items-center gap-2 px-5 py-2.5 bg-black/40 border-b border-white/[0.04]">
            {[
              { id: 'alerts', label: 'ALERT FEED & LOGS', icon: Bell },
              { id: 'devices', label: 'PAIRED DEVICES', icon: Smartphone },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); playHoverClick(); }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-wider transition-all ${activeTab === tab.id ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(0,229,255,0.2)]' : 'text-white/40 hover:text-white/80'}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}

            <div className="ml-auto flex items-center gap-2">
              <button
                onClick={() => handleTriggerTestAlert('PRODUCTIVITY_WARNING')}
                disabled={isTestTriggering}
                className="px-2.5 py-1 rounded bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 text-[9px] font-bold border border-yellow-500/30 transition-colors"
              >
                + TEST WARN
              </button>
              <button
                onClick={() => handleTriggerTestAlert('SECURITY_TAMPERING')}
                disabled={isTestTriggering}
                className="px-2.5 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-300 text-[9px] font-bold border border-red-500/30 transition-colors"
              >
                + TEST SECURITY
              </button>
            </div>
          </div>

          {/* Main Dashboard Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            {/* Status Cards (Section 7 Specification) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {/* Laptop State */}
              <div className="bg-black/40 p-3.5 rounded-xl border border-white/[0.06] relative overflow-hidden">
                <span className="text-[8px] text-white/40 uppercase block mb-1">Laptop Status</span>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse" />
                  <span className="text-xs font-bold text-white">ONLINE</span>
                </div>
                <span className="text-[8px] text-white/40 mt-1 block">Windows Agent Active</span>
              </div>

              {/* Protection Master Toggle */}
              <div className="bg-black/40 p-3.5 rounded-xl border border-white/[0.06] relative overflow-hidden">
                <span className="text-[8px] text-white/40 uppercase block mb-1">Protection Engine</span>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${data.protection_enabled ? 'bg-cyan-400 shadow-[0_0_8px_#22d3ee]' : 'bg-red-400'}`} />
                    <span className="text-xs font-bold text-white">
                      {data.protection_enabled ? 'ENABLED' : 'DISABLED'}
                    </span>
                  </div>
                  <button
                    onClick={handleToggleProtection}
                    className="text-[8px] px-1.5 py-0.5 rounded bg-white/10 hover:bg-white/20 text-white/70"
                  >
                    TOGGLE
                  </button>
                </div>
                <span className="text-[8px] text-white/40 mt-1 block">Deterministic Pipeline</span>
              </div>

              {/* Focus Mode */}
              <div className="bg-black/40 p-3.5 rounded-xl border border-white/[0.06] relative overflow-hidden">
                <span className="text-[8px] text-white/40 uppercase block mb-1">Focus Mode</span>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${data.focus_mode?.is_active ? 'bg-purple-400 shadow-[0_0_8px_#c084fc]' : 'bg-white/30'}`} />
                  <span className="text-xs font-bold text-white">
                    {data.focus_mode?.is_active ? data.focus_mode.mode : 'OFF'}
                  </span>
                </div>
                <span className="text-[8px] text-white/40 mt-1 block">Work Hours Policy</span>
              </div>

              {/* Overall Risk Level */}
              <div className="bg-black/40 p-3.5 rounded-xl border border-white/[0.06] relative overflow-hidden">
                <span className="text-[8px] text-white/40 uppercase block mb-1">Risk Status</span>
                <span className={`text-xs font-bold block ${data.metrics?.security_events_today > 0 ? 'text-red-400' : data.metrics?.violations_today > 0 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                  {data.metrics?.security_events_today > 0 ? 'CRITICAL' : data.metrics?.violations_today > 0 ? 'MEDIUM' : 'LOW'}
                </span>
                <span className="text-[8px] text-white/40 mt-1 block">Baseline Nominal</span>
              </div>
            </div>

            {/* TODAY Metric Counters (Section 7 Specification) */}
            <div className="bg-black/30 p-4 rounded-xl border border-white/[0.06]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[9px] font-bold uppercase tracking-wider text-cyan-400">TODAY METRICS</span>
                <span className="text-[8px] text-white/40">24-Hour Sliding Telemetry</span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="bg-black/40 p-2.5 rounded-lg border border-white/[0.04]">
                  <span className="text-base sm:text-lg font-bold text-yellow-400 block font-mono">
                    {data.metrics?.warnings_today || 0}
                  </span>
                  <span className="text-[8px] text-white/50 uppercase">Warnings</span>
                </div>
                <div className="bg-black/40 p-2.5 rounded-lg border border-white/[0.04]">
                  <span className="text-base sm:text-lg font-bold text-orange-400 block font-mono">
                    {data.metrics?.violations_today || 0}
                  </span>
                  <span className="text-[8px] text-white/50 uppercase">Violations</span>
                </div>
                <div className="bg-black/40 p-2.5 rounded-lg border border-white/[0.04]">
                  <span className="text-base sm:text-lg font-bold text-red-400 block font-mono">
                    {data.metrics?.security_events_today || 0}
                  </span>
                  <span className="text-[8px] text-white/50 uppercase">Security</span>
                </div>
                <div className="bg-black/40 p-2.5 rounded-lg border border-white/[0.04]">
                  <span className="text-base sm:text-lg font-bold text-cyan-400 block font-mono">
                    {data.metrics?.overrides_today || 0}
                  </span>
                  <span className="text-[8px] text-white/50 uppercase">Overrides</span>
                </div>
              </div>
            </div>

            {/* Tab: Recent Alerts Feed */}
            {activeTab === 'alerts' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                      RECENT MOBILE ALERTS ({filteredAlerts.length})
                    </h3>
                  </div>

                  {/* Filter Pills */}
                  <div className="flex items-center gap-1">
                    {['ALL', 'SECURITY', 'PRODUCTIVITY', 'UNREAD'].map((f) => (
                      <button
                        key={f}
                        onClick={() => setAlertFilter(f)}
                        className={`px-2 py-0.5 rounded text-[8px] font-bold transition-all ${alertFilter === f ? 'bg-cyan-500 text-black shadow-[0_0_8px_#22d3ee]' : 'bg-white/5 text-white/50 hover:text-white'}`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </div>

                {filteredAlerts.length === 0 ? (
                  <div className="p-8 text-center bg-black/20 rounded-xl border border-white/[0.04] space-y-2">
                    <ShieldCheck className="w-8 h-8 text-emerald-400/50 mx-auto" />
                    <p className="text-xs text-white/60 font-medium">No Alerts Recorded</p>
                    <p className="text-[9px] text-white/30 max-w-sm mx-auto">
                      All activities conform to configured policies. Whitelisted applications and developer tools remain local.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {filteredAlerts.map((alert) => (
                      <MobileAlertCard
                        key={alert.event_id}
                        alert={alert}
                        onAcknowledge={handleAcknowledge}
                        onOpenDetails={(a) => setSelectedAlert(a)}
                        onOverride={(a) => setSelectedAlert(a)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Device Manager */}
            {activeTab === 'devices' && (
              <MobileDeviceManager />
            )}
          </div>
        </motion.div>

        {/* Alert Details Modal */}
        <AlertDetailsModal
          isOpen={!!selectedAlert}
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onAcknowledge={async (id) => {
            await handleAcknowledge(id);
            setSelectedAlert(null);
          }}
          onExecuteAction={handleExecuteAction}
        />
      </div>
    </AnimatePresence>
  );
};

export default ProtectionDashboard;
