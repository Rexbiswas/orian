import React, { useEffect } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { useLogs } from '../context/LogContext';
import { Terminal, Activity, Database, Cpu, X, GripHorizontal } from 'lucide-react';

const NeuralLog = () => {
  const { logs, addLog, isLogOpen, setIsLogOpen } = useLogs();

  useEffect(() => {
    const events = [
      { msg: 'NEURAL_CORE_PULSE_SYNCED', type: 'SYS', status: 'SUCCESS' },
      { msg: 'RE-ROUTING_DATA_PATHWAY', type: 'NET', status: 'INFO' },
      { msg: 'CACHE_VALIDATION_COMPLETE', type: 'MEM', status: 'INFO' },
      { msg: 'ANOMALY_DETECTED_NULL', type: 'SYS', status: 'WARN' },
      { msg: 'LATENCY_OPTIMIZED', type: 'NET', status: 'SUCCESS' }
    ];

    const interval = setInterval(() => {
      if (Math.random() > 0.7 && isLogOpen) {
        const event = events[Math.floor(Math.random() * events.length)];
        addLog(event.msg, event.type, event.status);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [addLog, isLogOpen]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'SUCCESS': return 'text-emerald-500';
      case 'WARN': return 'text-amber-500';
      case 'ERROR': return 'text-red-500';
      case 'INFO': return 'text-brand-cyan';
      default: return 'text-slate-400';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'SYS': return <Cpu size={10} />;
      case 'NET': return <Activity size={10} />;
      case 'MEM': return <Database size={10} />;
      default: return <Terminal size={10} />;
    }
  };

  return (
    <Motion.div 
      drag
      dragMomentum={false}
      className="w-72 h-64 glass-morphism rounded-2xl flex flex-col overflow-hidden border border-brand-cyan/20 shadow-[0_0_40px_rgba(0,0,0,0.6)] cursor-default active:cursor-grabbing z-[100]"
    >
      {/* Header / Drag Handle */}
      <div className="px-3 py-2 border-b border-white/10 bg-white/5 flex items-center justify-between group/header">
        <div className="flex items-center gap-2">
          <GripHorizontal size={12} className="text-slate-600 group-hover/header:text-brand-cyan transition-colors" />
          <span className="text-[9px] font-black uppercase tracking-widest text-slate-300">Telemetry_Stream</span>
        </div>
        <button 
          onClick={() => setIsLogOpen(false)}
          className="p-1.5 hover:bg-white/10 rounded-lg text-slate-500 hover:text-red-400 transition-all"
        >
          <X size={14} />
        </button>
      </div>

      {/* Log Entries */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar font-mono">
        <AnimatePresence initial={false} mode="popLayout">
          {logs.map((log) => (
            <Motion.div
              key={log.id}
              layout
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: "spring", stiffness: 500, damping: 40 }}
              className="flex flex-col gap-1.5 border-l-2 border-brand-cyan/20 pl-3 py-1.5 hover:bg-white/5 transition-all group rounded-r-lg"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-[8px] font-bold text-slate-600 tabular-nums">[{log.timestamp}]</span>
                  <div className={`px-1.5 py-0.5 rounded text-[7px] font-black uppercase tracking-tighter bg-white/5 ${getStatusColor(log.status)}`}>
                    {log.type}
                  </div>
                </div>
                <div className="text-slate-600 opacity-20 group-hover:opacity-100 transition-opacity">
                  {getTypeIcon(log.type)}
                </div>
              </div>
              <div className="text-[10px] text-slate-300 leading-normal font-medium tracking-tight break-words">
                {log.message}
              </div>
            </Motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-white/10 bg-black/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
           <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
           <span className="text-[8px] text-slate-500 font-black uppercase tracking-[0.2em]">Live_Analysis_Running</span>
        </div>
        <div className="flex gap-1.5">
          {Array.from({ length: 4 }).map((_, i) => (
            <Motion.div 
              key={i}
              animate={{ 
                opacity: [0.2, 1, 0.2],
                scale: [1, 1.2, 1]
              }}
              transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
              className="w-1 h-1 rounded-full bg-brand-cyan"
            />
          ))}
        </div>
      </div>
    </Motion.div>

  );
};

export default NeuralLog;
