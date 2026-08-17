import React, { useState, useEffect } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Terminal, ShieldAlert, Cpu, Activity, ChevronDown, ChevronUp } from 'lucide-react';
import { getLastLatency, isTimeSynced } from '../../utils/timeSync';

const Metric = ({ label, val, color }) => (
  <div className="flex flex-col gap-0.5 p-2 rounded-lg bg-white/2 border border-white/5 hover:border-brand-cyan/20 transition-all group">
    <span className="text-[7px] font-black text-slate-500 uppercase tracking-widest group-hover:text-slate-400 transition-colors">{label}</span>
    <div className={`text-[10px] font-mono font-bold ${color}`}>{val}</div>
  </div>
);

const AIPanel = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [latency, setLatency] = useState("0.00ms");

  useEffect(() => {
    const timer = setInterval(() => {
      const realLatency = isTimeSynced() ? getLastLatency() : Math.random() * 0.1 + 0.05;
      setLatency(`${realLatency.toFixed(2)}ms`);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  return (
    <Motion.div 
      initial={false}
      animate={{ height: isExpanded ? 'auto' : '100px' }}
      className="w-72 glass-morphism rounded-2xl border border-brand-cyan/10 overflow-hidden shadow-[0_0_30px_rgba(0,242,255,0.05)]"
    >
      {/* Header / Compact View */}
      <div 
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-cyan/20 flex items-center justify-center text-brand-cyan">
            <Sparkles size={16} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-200">ORIAN_MK-IV</div>
            <div className="flex items-center gap-1.5">
               <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
               <span className="text-[7px] text-emerald-500 font-bold uppercase tracking-widest">Neural_Link_Ok</span>
            </div>
          </div>
        </div>
        <div className="text-slate-500 hover:text-brand-cyan transition-colors">
          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <Motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 pb-4 space-y-4"
          >
            <div className="h-[1px] bg-white/5 w-full" />
            
            {/* System Stats Grid */}
            <div className="grid grid-cols-2 gap-2">
              <Metric label="Latency" val={latency} color="text-brand-cyan" />
              <Metric label="Cores" val={navigator.hardwareConcurrency || "8"} color="text-brand-purple" />
              <Metric label="Load" val="12.4%" color="text-brand-blue" />
              <Metric label="Status" val="SECURE" color="text-emerald-500" />
            </div>

            <button className="w-full py-2 rounded-lg bg-red-600/10 border border-red-600/30 text-red-500 text-[8px] font-bold tracking-widest uppercase hover:bg-red-600 hover:text-white transition-all flex items-center justify-center gap-2">
              <ShieldAlert size={12} />
              Terminate Core
            </button>
          </Motion.div>
        )}
      </AnimatePresence>
    </Motion.div>
  );
};

export default AIPanel;
