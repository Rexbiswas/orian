import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShieldAlert, CheckCircle, Lock, Shield, Laptop, Clock, AlertTriangle, Key } from 'lucide-react';
import { playSuccessChime, playHoverClick } from '../../utils/sound';

const AlertDetailsModal = ({ isOpen, alert, onClose, onAcknowledge, onExecuteAction }) => {
  const [overridePassword, setOverridePassword] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverrideInput, setShowOverrideInput] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionError, setActionError] = useState('');

  if (!isOpen || !alert) return null;

  const handleAcknowledge = async () => {
    if (onAcknowledge) {
      await onAcknowledge(alert.event_id);
      playSuccessChime();
    }
  };

  const handleSubmitOverride = async (e) => {
    e.preventDefault();
    setActionError('');
    setIsProcessing(true);
    try {
      if (onExecuteAction) {
        await onExecuteAction({
          event_id: alert.event_id,
          action_type: 'OWNER_OVERRIDE',
          reason: overrideReason || 'Manual owner override from modal',
          password: overridePassword
        });
        playSuccessChime();
        setShowOverrideInput(false);
        setOverridePassword('');
        setOverrideReason('');
      }
    } catch (err) {
      setActionError(err.response?.data?.detail || err.message || 'Override authentication failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const timeFormatted = alert.timestamp
    ? new Date(alert.timestamp * 1000).toLocaleString()
    : 'Unknown';

  const isResolved = alert.status === 'ACKNOWLEDGED';

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 15 }}
          className="relative w-full max-w-lg rounded-2xl bg-[#030712] border border-cyan-500/30 shadow-[0_0_50px_rgba(0,229,255,0.15)] overflow-hidden font-mono"
        >
          {/* Top header glow */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />

          {/* Modal Header */}
          <div className="flex items-center justify-between p-4 border-b border-white/[0.08] bg-white/[0.02]">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                <ShieldAlert className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-300">
                  {alert.title || 'ORIAN SECURITY EVENT'}
                </h3>
                <p className="text-[10px] text-white/40">Event Verification & Audit Record</p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Modal Body: Complete Section 8 Specifications */}
          <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
            {/* Event Summary Grid */}
            <div className="grid grid-cols-2 gap-3 text-[11px] bg-black/40 p-4 rounded-xl border border-white/[0.06]">
              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Event ID</span>
                <span className="text-cyan-400 font-bold text-[10px] select-all truncate block">
                  {alert.event_id}
                </span>
              </div>
              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Device</span>
                <span className="text-white/90 truncate block">{alert.device_id || 'My Windows Laptop'}</span>
              </div>

              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Category</span>
                <span className="text-amber-300 truncate block">
                  {alert.type ? alert.type.replace(/_/g, ' ') : 'Security'}
                </span>
              </div>
              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Risk Level</span>
                <span className={`font-bold uppercase ${alert.risk === 'CRITICAL' ? 'text-red-400' : alert.risk === 'HIGH' ? 'text-orange-400' : 'text-yellow-400'}`}>
                  {alert.risk || 'LOW'}
                </span>
              </div>

              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Activity</span>
                <span className="text-white/90 font-medium truncate block">{alert.activity || 'Activity Signal'}</span>
              </div>
              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Policy</span>
                <span className="text-white/90 truncate block">{alert.policy_name || alert.policy_id || 'Security Protection'}</span>
              </div>

              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Detection Source</span>
                <span className="text-white/80">Windows Agent (Win32)</span>
              </div>
              <div>
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Action Enforced</span>
                <span className={`font-bold ${alert.action === 'Blocked' ? 'text-red-400' : 'text-cyan-400'}`}>
                  {alert.action || 'Warning issued'}
                </span>
              </div>

              <div className="col-span-2 pt-2 border-t border-white/[0.04]">
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Timestamp</span>
                <span className="text-white/70 text-[10px]">{timeFormatted}</span>
              </div>

              <div className="col-span-2">
                <span className="text-[9px] text-white/40 uppercase block mb-0.5">Status</span>
                <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[9px] font-bold ${isResolved ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
                  {isResolved ? 'RESOLVED' : 'UNREAD / PENDING'}
                </span>
              </div>
            </div>

            {/* Detailed Reason */}
            {alert.reason && (
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/[0.04]">
                <span className="text-[9px] text-white/40 uppercase block mb-1">Reason & Context</span>
                <p className="text-[10px] text-white/80 leading-relaxed">{alert.reason}</p>
              </div>
            )}

            {/* Override Section with Authentication */}
            {showOverrideInput && (
              <motion.form
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                onSubmit={handleSubmitOverride}
                className="bg-red-950/20 p-4 rounded-xl border border-red-500/30 space-y-3"
              >
                <div className="flex items-center gap-1.5 text-red-400 text-[10px] font-bold">
                  <Lock className="w-3.5 h-3.5" />
                  AUTHENTICATED OWNER OVERRIDE REQUIRED
                </div>
                <p className="text-[9px] text-white/60">
                  Privileged override requires administrator/owner password or TOTP verification.
                </p>

                <input
                  type="text"
                  placeholder="Override Reason (Optional)"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-black/60 border border-white/10 text-white text-[10px] focus:outline-none focus:border-red-500"
                />

                <input
                  type="password"
                  placeholder="Owner Master Password"
                  value={overridePassword}
                  onChange={(e) => setOverridePassword(e.target.value)}
                  required
                  className="w-full px-3 py-1.5 rounded bg-black/60 border border-white/10 text-white text-[10px] focus:outline-none focus:border-red-500"
                />

                {actionError && (
                  <p className="text-[9px] text-red-400 font-bold">{actionError}</p>
                )}

                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setShowOverrideInput(false)}
                    className="px-3 py-1 text-[9px] text-white/50 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isProcessing}
                    className="px-4 py-1 rounded bg-red-600 hover:bg-red-500 text-white text-[10px] font-bold shadow-[0_0_12px_rgba(239,68,68,0.4)] disabled:opacity-50"
                  >
                    {isProcessing ? 'Verifying...' : 'Authorize Override'}
                  </button>
                </div>
              </motion.form>
            )}
          </div>

          {/* Modal Footer Controls */}
          <div className="flex items-center justify-between p-4 border-t border-white/[0.08] bg-white/[0.02]">
            {!showOverrideInput && (
              <button
                onClick={() => setShowOverrideInput(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-bold border border-red-500/30 transition-colors"
              >
                <Key className="w-3.5 h-3.5" />
                OWNER OVERRIDE
              </button>
            )}

            <div className="flex items-center gap-2 ml-auto">
              {!isResolved && (
                <button
                  onClick={handleAcknowledge}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[10px] font-bold border border-cyan-500/40 shadow-[0_0_15px_rgba(0,229,255,0.2)] transition-all"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                  ACKNOWLEDGE
                </button>
              )}
              <button
                onClick={onClose}
                className="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-white/70 text-[10px] transition-colors"
              >
                CLOSE
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default AlertDetailsModal;
