import React from 'react';

const AIModeCards = () => {
  const modes = [
    { 
      label: "AI Mode", 
      val: "AUTONOMOUS", 
      color: "text-[#00FF66] shadow-[0_0_10px_rgba(0,255,102,0.15)] hover:shadow-[0_0_15px_rgba(0,255,102,0.3)]",
      borderColor: "border-[#00FF66]/20 hover:border-[#00FF66]/50" 
    },
    { 
      label: "Personality", 
      val: "ADAPTIVE", 
      color: "text-[#00E5FF] shadow-[0_0_10px_rgba(0,229,255,0.15)] hover:shadow-[0_0_15px_rgba(0,229,255,0.3)]",
      borderColor: "border-[#00E5FF]/20 hover:border-[#00E5FF]/50" 
    },
    { 
      label: "Task Priority", 
      val: "HIGH", 
      color: "text-[#FF007F] shadow-[0_0_10px_rgba(255,0,127,0.15)] hover:shadow-[0_0_15px_rgba(255,0,127,0.3)]",
      borderColor: "border-[#FF007F]/20 hover:border-[#FF007F]/50" 
    },
    { 
      label: "Learning Mode", 
      val: "CONTINUOUS", 
      color: "text-[#00FFCC] shadow-[0_0_10px_rgba(0,255,204,0.15)] hover:shadow-[0_0_15px_rgba(0,255,204,0.3)]",
      borderColor: "border-[#00FFCC]/20 hover:border-[#00FFCC]/50" 
    }
  ];

  return (
    <div className="w-full grid grid-cols-4 gap-2.5 border-t border-purple-500/10 pt-4">
      {modes.map(badge => (
        <div 
          key={badge.label} 
          className={`border rounded-[6px] px-2 py-2.5 flex flex-col items-center justify-center bg-[#050A18]/50 backdrop-blur-md transition-all duration-300 transform hover:scale-[1.04] cursor-pointer select-none ${badge.borderColor}`}
        >
          <span className="text-[6.5px] font-semibold uppercase tracking-wider text-slate-400 leading-none mb-1.5">
            {badge.label}
          </span>
          <span className={`text-[9px] font-black tracking-widest leading-none font-sans ${badge.color}`}>
            {badge.val}
          </span>
        </div>
      ))}
    </div>
  );
};

export default AIModeCards;
