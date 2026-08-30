import React from 'react';

const statusBadge = (status) => {
  switch (status?.toLowerCase()) {
    case 'running':   return 'status-badge-active';
    case 'completed': return 'status-badge-online';
    case 'paused':    return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    default:          return 'status-badge-idle';
  }
};

const ProgressBar = ({ label, value, isPurple = false, status = "" }) => {
  const fillColor = isPurple
    ? 'bg-gradient-to-r from-purple-700 to-purple-400'
    : value === 100
      ? 'bg-gradient-to-r from-emerald-600 to-emerald-400'
      : 'bg-gradient-to-r from-cyan-600 to-cyan-300';

  const glowColor = isPurple
    ? 'shadow-[0_0_6px_rgba(168,85,247,0.6)]'
    : value === 100
      ? 'shadow-[0_0_6px_rgba(52,211,153,0.6)]'
      : 'shadow-[0_0_6px_rgba(0,229,255,0.6)]';

  return (
    <div className="flex flex-col gap-0.5 w-full">
      <div className="flex justify-between items-center text-[6.5px] font-black uppercase tracking-wider leading-none mb-0.5">
        <span className="text-slate-400">{label}</span>
        <div className="flex items-center gap-1.5">
          {status && (
            <span className={`px-1.5 py-0.5 rounded-sm text-[5.5px] font-black tracking-widest ${statusBadge(status)}`}>
              {status}
            </span>
          )}
          <span className="text-white tabular-nums">{value}%</span>
        </div>
      </div>
      <div className="h-[3px] bg-white/[0.06] rounded-full overflow-hidden border border-white/[0.04]">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${fillColor} ${glowColor}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
