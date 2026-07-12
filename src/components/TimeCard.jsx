import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

const TimeCard = () => {
  const [timeState, setTimeState] = useState(new Date());

  useEffect(() => {
    const clock = setInterval(() => setTimeState(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  const formattedTime = timeState.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  const formattedDay = timeState.toLocaleDateString([], { weekday: 'long' });
  const formattedDate = timeState.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <div className="w-1/2 flex items-center gap-3.5 pl-2 h-full">
      <div className="w-9 h-9 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 shrink-0">
        <Clock size={16} />
      </div>
      <div className="flex flex-col justify-center">
        <span className="text-[6.5px] font-black text-slate-500 uppercase tracking-widest mb-1.5 block">Time Center</span>
        <span className="text-[10px] font-bold text-white tracking-widest leading-none mb-1">
          {formattedTime}
        </span>
        <span className="text-[7.5px] text-cyan-400 leading-none font-bold">
          {formattedDay}, {formattedDate}
        </span>
      </div>
    </div>
  );
};

export default TimeCard;
