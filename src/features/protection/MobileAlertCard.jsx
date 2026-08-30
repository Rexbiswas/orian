import React from 'react';
import { motion } from 'framer-motion';
import { 
  Bell, ShieldAlert, Laptop, AlertTriangle, Smartphone, 
  Power, CheckCircle, ShieldCheck, Gamepad2, Eye, Lock
} from 'lucide-react';
import { playHoverClick } from '../../utils/sound';

const getRiskTheme = (risk) => {
  const r = (risk || 'LOW').toUpperCase();
  if (r === 'CRITICAL') {
    return {
      bg: 'bg-red-950/40 border-red-500/50 shadow-[0_0_25px_rgba(239,68,68,0.25)]',
      badge: 'bg-red-500/20 text-red-400 border-red-500/40',
      iconColor: 'text-red-400',
      sheen: 'via-red-500/30'
    };
  }
  if (r === 'HIGH') {
    return {
      bg: 'bg-amber-950/40 border-orange-500/50 shadow-[0_0_20px_rgba(249,115,22,0.2)]',
      badge: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
      iconColor: 'text-orange-400',
      sheen: 'via-orange-500/30'
    };
  }
  if (r === 'MEDIUM') {
    return {
      bg: 'bg-yellow-950/30 border-yellow-500/40 shadow-[0_0_18px_rgba(234,179,8,0.15)]',
      badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      iconColor: 'text-yellow-400',
      sheen: 'via-yellow-400/25'
    };
  }
  return {
    bg: 'bg-emerald-950/30 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.12)]',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    iconColor: 'text-emerald-400',
    sheen: 'via-emerald-400/20'
  };
};

const getCategoryIcon = (type) => {
  const t = (type || '').toUpperCase();
  if (t.includes('GAMING')) return <Gamepad2 className="w-4 h-4 text-yellow-400" />;
  if (t.includes('SECURITY') || t.includes('TAMPERING') || t.includes('MALWARE') || t.includes('HACKING')) {
    return <ShieldAlert className="w-4 h-4 text-red-400 animate-pulse" />;
  }
  if (t.includes('SLEEP')) return <Power className="w-4 h-4 text-cyan-400" />;
  if (t.includes('DEVICE')) return <Smartphone className="w-4 h-4 text-indigo-400" />;
  if (t.includes('BLOCKED')) return <AlertTriangle className="w-4 h-4 text-orange-400" />;
  return <Bell className="w-4 h-4 text-cyan-400" />;
};

const MobileAlertCard = ({ alert, onAcknowledge, onOpenDetails, onOverride }) => {
  if (!alert) return null;

  const theme = getRiskTheme(alert.risk);
  const timeStr = alert.timestamp 
    ? new Date(alert.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : 'Just now';

  const isAcknowledged = alert.status === 'ACKNOWLEDGED';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ scale: 1.01 }}
      onMouseEnter={() => playHoverClick()}
      className={`relative rounded-xl p-3.5 border backdrop-blur-xl transition-all duration-200 ${theme.bg}`}
    >
      {/* Top Sheen Line */}
      <div className={`absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent ${theme.sheen} to-transparent`} />

      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-lg bg-black/40 border border-white/10">
            {getCategoryIcon(alert.type)}
          </div>
          <div>
            <h4 className="text-[11px] font-bold tracking-wider uppercase font-mono text-white/90">
              {alert.title || 'ORIAN ALERT'}
            </h4>
            <p className="text-[9px] text-white/50 font-mono">
              {alert.type ? alert.type.replace(/_/g, ' ') : 'POLICY NOTIFICATION'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold font-mono border ${theme.badge}`}>
            {alert.risk || 'LOW'}
          </span>
          <span className="text-[9px] font-mono text-white/40">{timeStr}</span>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mb-3 bg-black/30 p-2.5 rounded-lg border border-white/[0.04]">
        <div>
          <span className="text-white/40 block text-[8px] uppercase">Activity</span>
          <span className="text-white/90 font-medium truncate block">
            {alert.activity || 'Activity Triggered'}
          </span>
        </div>
        <div>
          <span className="text-white/40 block text-[8px] uppercase">Policy</span>
          <span className="text-white/90 font-medium truncate block">
            {alert.policy_name || alert.policy_id || 'Protection Policy'}
          </span>
        </div>
        <div>
          <span className="text-white/40 block text-[8px] uppercase">Action</span>
          <span className={`font-semibold truncate block ${alert.action === 'Blocked' ? 'text-red-400' : alert.action?.includes('sleep') ? 'text-cyan-400' : 'text-amber-400'}`}>
            {alert.action || 'Warning issued'}
          </span>
        </div>
        <div>
          <span className="text-white/40 block text-[8px] uppercase">Device</span>
          <span className="text-white/80 truncate block">
            {alert.device_id || 'My Windows Laptop'}
          </span>
        </div>
      </div>

      {/* Reason text if available */}
      {alert.reason && (
        <p className="text-[9px] font-mono text-white/70 bg-white/[0.02] p-1.5 rounded border border-white/[0.03] mb-3 leading-relaxed">
          {alert.reason}
        </p>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-2 pt-1">
        <button
          onClick={() => onOpenDetails && onOpenDetails(alert)}
          className="flex items-center gap-1 px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-white/70 hover:text-white text-[9px] font-mono transition-colors border border-white/10"
        >
          <Eye className="w-3 h-3 text-cyan-400" />
          DETAILS
        </button>

        <div className="flex items-center gap-1.5">
          {!isAcknowledged ? (
            <button
              onClick={() => onAcknowledge && onAcknowledge(alert.event_id)}
              className="flex items-center gap-1 px-3 py-1 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[9px] font-mono font-bold transition-colors border border-cyan-500/40"
            >
              <CheckCircle className="w-3 h-3" />
              ACKNOWLEDGE
            </button>
          ) : (
            <span className="flex items-center gap-1 text-[9px] font-mono text-emerald-400/80 px-2 py-0.5 bg-emerald-500/10 rounded border border-emerald-500/20">
              <ShieldCheck className="w-3 h-3" />
              RESOLVED
            </span>
          )}

          {alert.risk === 'HIGH' || alert.risk === 'CRITICAL' ? (
            <button
              onClick={() => onOverride && onOverride(alert)}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-300 text-[9px] font-mono transition-colors border border-red-500/40"
            >
              <Lock className="w-3 h-3" />
              OVERRIDE
            </button>
          ) : null}
        </div>
      </div>
    </motion.div>
  );
};

export default MobileAlertCard;
