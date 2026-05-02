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
    <AnimatePresence>
      {isLogOpen && (
        <Motion.div 
          drag
          dragMomentum={false}
          initial={{ opacity: 0, scale: 0.9, x: -20, filter: "blur(10px)" }}
          animate={{ opacity: 1, scale: 1, x: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, scale: 0.9, x: -20, filter: "blur(10px)" }}
          className="w-64 h-80 glass-morphism rounded-2xl flex flex-col overflow-hidden border border-brand-cyan/20 shadow-[0_20px_50px_rgba(0,0,0,0.5)] cursor-default active:cursor-grabbing z-[100]"
        >
          {/* Header / Drag Handle */}
          <div className="px-4 py-3 border-b border-white/5 bg-white/5 flex items-center justify-between group/header">
            <div className="flex items-center gap-2">
              <GripHorizontal size={14} className="text-slate-600 group-hover/header:text-brand-cyan transition-colors" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Neural_Telemetry</span>
            </div>
            <button 
              onClick={() => setIsLogOpen(false)}
              className="p-1 hover:bg-white/10 rounded-md text-slate-500 hover:text-red-400 transition-all"
            >
              <X size={14} />
            </button>
          </div>

          {/* Log Entries */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2 no-scrollbar font-mono text-[9px]">
            <AnimatePresence initial={false}>
              {logs.map((log) => (
                <Motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -20, height: 0 }}
                  animate={{ opacity: 1, x: 0, height: 'auto' }}
                  className="flex flex-col gap-1 border-l border-white/10 pl-2 py-1 hover:bg-white/5 transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-600">[{log.timestamp}]</span>
                      <span className={`${getStatusColor(log.status)} font-bold`}>{log.type}</span>
                    </div>
                    <div className="text-slate-700 opacity-0 group-hover:opacity-100 transition-opacity">
                      {getTypeIcon(log.type)}
                    </div>
                  </div>
                  <div className="text-slate-400 leading-tight">
                    {log.message}
                  </div>
                </Motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Footer */}
          <div className="px-3 py-2 border-t border-white/5 bg-black/20 flex items-center justify-between">
            <div className="text-[7px] text-slate-600 font-bold uppercase tracking-widest">Buffer_Active</div>
            <div className="flex gap-1">
              {Array.from({ length: 4 }).map((_, i) => (
                <Motion.div 
                  key={i}
                  animate={{ opacity: [0.2, 1, 0.2] }}
                  transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                  className="w-1.5 h-1.5 rounded-full bg-brand-cyan/40"
                />
              ))}
            </div>
          </div>
        </Motion.div>
      )}
    </AnimatePresence>
  );
};

export default NeuralLog;
