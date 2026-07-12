import React from 'react';

const StatCard = ({ label, value, icon: Icon, color = "text-cyan-400" }) => {
  return (
    <div className="flex items-center gap-2.5 px-4 border-r border-white/5 last:border-none">
      <div className="w-7 h-7 rounded-lg bg-white/2 border border-white/5 flex items-center justify-center text-slate-400">
        {Icon && <Icon size={11} className={color} />}
      </div>
      <div className="flex flex-col">
        <span className="text-[6.5px] font-black text-slate-500 uppercase tracking-widest leading-none mb-1">{label}</span>
        <span className={`text-[10px] font-mono font-bold leading-none ${color}`}>{value}</span>
      </div>
    </div>
  );
};

export default StatCard;
