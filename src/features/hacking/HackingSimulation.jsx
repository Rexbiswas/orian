import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Terminal, Activity, Zap, Lock, Unlock, Database, Cpu } from 'lucide-react';
import axios from 'axios';

const HackingSimulation = ({ onClose }) => {
  const [logs, setLogs] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [breachProgress, setBreachProgress] = useState(0);
  const [activeNodes, setActiveNodes] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      if (scanning) {
        const newLog = {
          id: Date.now(),
          text: `[NEURAL_SCAN] NODE_${Math.floor(Math.random() * 9999)}: ${Math.random() > 0.5 ? 'HANDSHAKE_ESTABLISHED' : 'BYPASSING_FIREWALL...'}`,
          type: Math.random() > 0.8 ? 'alert' : 'info'
        };
        setLogs(prev => [newLog, ...prev].slice(0, 15));
        setBreachProgress(p => (p >= 100 ? 0 : p + 1));
        setActiveNodes(Math.floor(Math.random() * 50));
      }
    }, 800);
    return () => clearInterval(interval);
  }, [scanning]);

  const startSimulation = () => {
    setScanning(true);
    setLogs([{ id: 1, text: "INITIALIZING_HACKING_SIMULATION_V1.0", type: 'info' }]);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 20 }}
      className="fixed bottom-24 right-96 w-80 h-[450px] bg-black/80 border border-brand-purple/30 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.2)] backdrop-blur-xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-brand-purple/20 flex justify-between items-center bg-brand-purple/5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-brand-purple/20 rounded-lg">
            <Shield size={16} className="text-brand-purple animate-pulse" />
          </div>
          <div>
            <h2 className="text-xs font-black text-white tracking-widest uppercase">Hacking_Sim</h2>
            <div className="flex items-center gap-1">
              <div className={`w-1 h-1 rounded-full ${scanning ? 'bg-green-500 animate-ping' : 'bg-red-500'}`} />
              <span className="text-[8px] text-slate-500 font-bold uppercase">{scanning ? 'Active_Link' : 'Offline'}</span>
            </div>
          </div>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
          <Lock size={14} />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-px bg-white/5 border-b border-white/5">
        <div className="p-3 flex flex-col items-center">
          <span className="text-[7px] text-slate-500 uppercase font-black mb-1">Breach_Depth</span>
          <span className="text-sm font-mono text-brand-purple">{breachProgress}%</span>
        </div>
        <div className="p-3 flex flex-col items-center border-l border-white/5">
          <span className="text-[7px] text-slate-500 uppercase font-black mb-1">Active_Nodes</span>
          <span className="text-sm font-mono text-brand-cyan">{activeNodes}</span>
        </div>
      </div>

      {/* Terminal View */}
      <div className="flex-1 p-4 font-mono text-[10px] overflow-y-auto no-scrollbar space-y-1 bg-black/40">
        {logs.map(log => (
          <div key={log.id} className={`${log.type === 'alert' ? 'text-brand-purple' : 'text-brand-cyan/70'} leading-tight`}>
            {log.text}
          </div>
        ))}
        {!scanning && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
            <Terminal size={32} className="text-slate-700" />
            <p className="text-slate-500 text-[9px] uppercase tracking-tighter px-6">
              Security clearance detected. Initializing Orian's Hacking Repository requires neural confirmation.
            </p>
            <button 
              onClick={startSimulation}
              className="px-6 py-2 bg-brand-purple/10 border border-brand-purple/30 rounded-full text-brand-purple text-[10px] font-black uppercase hover:bg-brand-purple/20 transition-all"
            >
              Initialize_Link
            </button>
          </div>
        )}
      </div>

      {/* Footer Metrics */}
      <div className="p-4 bg-brand-purple/5 border-t border-brand-purple/10 space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <Cpu size={12} className="text-slate-500" />
            <Activity size={12} className="text-slate-500" />
            <Database size={12} className="text-slate-500" />
          </div>
          <span className="text-[9px] font-black text-brand-purple uppercase italic">Orian_Sec_Core</span>
        </div>
        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
          <motion.div 
            animate={{ x: scanning ? ["-100%", "100%"] : "0%" }}
            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
            className="h-full w-1/3 bg-gradient-to-r from-transparent via-brand-purple to-transparent"
          />
        </div>
      </div>
    </motion.div>
  );
};

export default HackingSimulation;
