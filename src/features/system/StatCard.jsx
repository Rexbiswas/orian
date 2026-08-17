import React from 'react';

const StatCard = ({ label, value, percentage = 40, icon: Icon, color = "text-cyan-400", glowColor = "rgba(0,229,255,0.4)" }) => {
  // Circular progress math
  const radius = 10;
  const strokeWidth = 1.8;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex items-center gap-3 px-4 border-r border-white/5 last:border-none">
      <div className="relative w-7 h-7 flex items-center justify-center">
        {/* Animated circular progress ring */}
        <svg className="w-7 h-7 transform -rotate-90 absolute">
          {/* Background Track */}
          <circle
            cx="14"
            cy="14"
            r={radius}
            className="stroke-white/5 fill-none"
            strokeWidth={strokeWidth}
          />
          {/* Active Ring */}
          <circle
            cx="14"
            cy="14"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={`${color} fill-none transition-all duration-500`}
            style={{ filter: `drop-shadow(0 0 3px ${glowColor})` }}
          />
        </svg>
        {/* Icon in center */}
        <div className="relative z-10 text-slate-300 scale-90">
          {Icon && <Icon size={10} />}
        </div>
      </div>
      <div className="flex flex-col font-mono">
        <span className="text-[6.5px] font-black text-slate-500 uppercase tracking-widest leading-none mb-1">{label}</span>
        <span className={`text-[10px] font-bold leading-none ${color}`}>{value}</span>
      </div>
    </div>
  );
};

export default StatCard;
