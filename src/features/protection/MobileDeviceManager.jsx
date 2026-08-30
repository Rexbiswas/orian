import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Smartphone, Laptop, ShieldCheck, ShieldAlert, Plus, Trash2, RefreshCw, CheckCircle, Lock } from 'lucide-react';
import { API_BASE_URL } from '../../config';
import { playSuccessChime, playHoverClick } from '../../utils/sound';

const MobileDeviceManager = () => {
  const [mobileDevices, setMobileDevices] = useState([]);
  const [laptopDevices, setLaptopDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newDeviceName, setNewDeviceName] = useState('');
  const [pairingSuccess, setPairingSuccess] = useState(null);
  const [error, setError] = useState('');

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const [mobRes, lapRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/mobile/devices`).catch(() => ({ data: { devices: [] } })),
        axios.get(`${API_BASE_URL}/api/laptop/status`).catch(() => ({ data: { devices: [] } }))
      ]);
      setMobileDevices(mobRes.data.devices || []);
      setLaptopDevices(lapRes.data.devices || []);
    } catch (err) {
      console.error("Failed to load devices:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handlePairMobile = async (e) => {
    e.preventDefault();
    if (!newDeviceName.trim()) return;
    setError('');
    try {
      const devId = `mob-${Date.now().toString(36)}`;
      const res = await axios.post(`${API_BASE_URL}/api/mobile/register`, {
        device_id: devId,
        device_name: newDeviceName
      });
      if (res.data.success) {
        setPairingSuccess({
          device_id: res.data.device_id,
          pairing_code: res.data.pairing_code,
          name: newDeviceName
        });
        setNewDeviceName('');
        playSuccessChime();
        fetchDevices();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Registration failed");
    }
  };

  const handleApprove = async (deviceId, isMobile = true) => {
    try {
      const token = localStorage.getItem('orian_token') || 'mock_token';
      const endpoint = isMobile ? '/api/mobile/approve' : '/api/laptop/approve';
      await axios.post(`${API_BASE_URL}${endpoint}`, {
        device_id: deviceId,
        approved: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSuccessChime();
      fetchDevices();
    } catch (err) {
      console.error("Approval error:", err);
    }
  };

  const handleRevoke = async (deviceId, isMobile = true) => {
    if (!window.confirm("Are you sure you want to permanently revoke this device's privileged access?")) return;
    try {
      const token = localStorage.getItem('orian_token') || 'mock_token';
      const endpoint = isMobile ? '/api/mobile/revoke' : '/api/laptop/revoke';
      await axios.post(`${API_BASE_URL}${endpoint}`, {
        device_id: deviceId,
        reason: "Revoked by owner via Dashboard"
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSuccessChime();
      fetchDevices();
    } catch (err) {
      console.error("Revocation error:", err);
    }
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400">
            PAIRED HARDWARE & MOBILE CLIENTS
          </h3>
          <p className="text-[10px] text-white/40">Cryptographically Registered Endpoint Identities</p>
        </div>
        <button
          onClick={fetchDevices}
          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* New Mobile Pairing Card */}
      <form onSubmit={handlePairMobile} className="bg-black/30 p-3.5 rounded-xl border border-white/[0.06] space-y-2">
        <span className="text-[9px] uppercase tracking-wider text-white/50 block">Pair New Mobile Phone</span>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="e.g. Owner iPhone 16 / Pixel 9"
            value={newDeviceName}
            onChange={(e) => setNewDeviceName(e.target.value)}
            className="flex-1 px-3 py-1.5 rounded bg-black/60 border border-white/10 text-white text-[10px] focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            className="flex items-center gap-1 px-3 py-1.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[10px] font-bold border border-cyan-500/40 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            PAIR
          </button>
        </div>
        {error && <p className="text-[9px] text-red-400">{error}</p>}
        {pairingSuccess && (
          <div className="p-2.5 rounded bg-cyan-950/40 border border-cyan-500/30 text-[10px] text-cyan-300 space-y-1">
            <p className="font-bold">Pairing Initiated for "{pairingSuccess.name}"!</p>
            <p className="text-[9px] text-white/70">Pairing Code: <span className="text-white font-bold tracking-widest">{pairingSuccess.pairing_code}</span></p>
          </div>
        )}
      </form>

      {/* Mobile Devices List */}
      <div className="space-y-2">
        <span className="text-[9px] uppercase tracking-wider text-white/50 block flex items-center gap-1">
          <Smartphone className="w-3 h-3 text-cyan-400" />
          Mobile Phone Endpoints ({mobileDevices.length})
        </span>

        {mobileDevices.length === 0 ? (
          <div className="p-4 text-center text-white/30 text-[10px] bg-black/20 rounded-lg border border-white/[0.04]">
            No mobile devices paired yet.
          </div>
        ) : (
          mobileDevices.map((d) => (
            <div
              key={d.device_id}
              className="flex items-center justify-between p-3 rounded-lg bg-black/40 border border-white/[0.06] text-[10px]"
            >
              <div className="flex items-center gap-2.5">
                <Smartphone className={`w-4 h-4 ${d.status === 'ACTIVE' ? 'text-emerald-400' : d.status === 'REVOKED' ? 'text-red-400' : 'text-yellow-400'}`} />
                <div>
                  <span className="font-bold text-white/90 block">{d.device_name}</span>
                  <span className="text-[8px] text-white/40 block truncate max-w-[140px]">{d.device_id}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${d.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : d.status === 'REVOKED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'}`}>
                  {d.status}
                </span>

                {d.status === 'PAIRING' && (
                  <button
                    onClick={() => handleApprove(d.device_id, true)}
                    className="px-2 py-0.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[8px] font-bold border border-cyan-500/40"
                  >
                    APPROVE
                  </button>
                )}

                {d.status !== 'REVOKED' && (
                  <button
                    onClick={() => handleRevoke(d.device_id, true)}
                    className="p-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
                    title="Revoke Device"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Windows Laptops List */}
      <div className="space-y-2 pt-2 border-t border-white/[0.06]">
        <span className="text-[9px] uppercase tracking-wider text-white/50 block flex items-center gap-1">
          <Laptop className="w-3 h-3 text-cyan-400" />
          Windows Workstations ({laptopDevices.length})
        </span>

        {laptopDevices.map((d) => (
          <div
            key={d.device_id}
            className="flex items-center justify-between p-3 rounded-lg bg-black/40 border border-white/[0.06] text-[10px]"
          >
            <div className="flex items-center gap-2.5">
              <Laptop className={`w-4 h-4 ${d.status === 'ACTIVE' ? 'text-cyan-400' : 'text-yellow-400'}`} />
              <div>
                <span className="font-bold text-white/90 block">{d.device_name}</span>
                <span className="text-[8px] text-white/40 block">{d.device_id} (v{d.agent_version})</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${d.status === 'ACTIVE' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'}`}>
                {d.status}
              </span>

              {d.status === 'PAIRING' && (
                <button
                  onClick={() => handleApprove(d.device_id, false)}
                  className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[8px] font-bold border border-cyan-500/40"
                >
                  APPROVE
                </button>
              )}

              {d.status !== 'REVOKED' && (
                <button
                  onClick={() => handleRevoke(d.device_id, false)}
                  className="p-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MobileDeviceManager;
