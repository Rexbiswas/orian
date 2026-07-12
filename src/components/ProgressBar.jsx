import React from 'react';

const ProgressBar = ({ label, value, isPurple = false, status = "" }) => {
  const fillColor = isPurple 
    ? 'bg-gradient-to-r from-purple-600 to-purple-400 shadow-[0_0_8px_#8a2be2]' 
    : 'bg-gradient-to-r from-cyan-500 to-cyan-300 shadow-[0_0_8px_#00e5ff]';

  const textTheme = isPurple ? 'text-purple-400' : 'text-cyan-400';

  return (
    <div className="flex flex-col gap-0.5 w-full">
      <div className="flex justify-between text-[6.5px] font-black uppercase tracking-wider leading-none">
        <span className="text-slate-400">{label}</span>
        <div className="flex items-center gap-1.5 font-mono">
          {status && <span className={textTheme}>{status}</span>}
          <span className="text-white">{value}%</span>
        </div>
      </div>
      <div className="h-[4px] bg-white/5 rounded-full overflow-hidden border border-white/5">
        <div 
          className={`h-full rounded-full transition-all duration-700 ease-out ${fillColor}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
