import React, { useState, useEffect } from 'react';
import { Bot } from 'lucide-react';

const AgentCard = () => {
  const [task, setTask] = useState('Orchestrating system layout and responsive design...');
  const [thoughtDepth, setThoughtDepth] = useState(98);

  // Simulate thinking state changes occasionally to look alive
  useEffect(() => {
    const tasks = [
      'Orchestrating system layout and responsive design...',
      'Monitoring neural network weights and optimization...',
      'Analyzing screen layouts for visual defects...',
      'Syncing system parameters with central AI base...',
      'Standby. Listening for next user command...'
    ];

    const interval = setInterval(() => {
      const randomTask = tasks[Math.floor(Math.random() * tasks.length)];
      setTask(randomTask);
      setThoughtDepth(Math.floor(85 + Math.random() * 15));
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full lg:w-[100%] flex items-center gap-3.5 pl-2 h-full min-w-0">
      <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0 shadow-[0_0_12px_rgba(168,85,247,0.2)]">
        <Bot size={16} className="animate-pulse" />
      </div>
      <div className="flex flex-col justify-center min-w-0 w-full">
        <span className="text-[6.5px] font-black text-purple-400 uppercase tracking-widest mb-1.5 block">AI Agent Co-Pilot</span>
        <span className="text-[9px] font-bold text-white uppercase tracking-wider leading-none mb-1 truncate">
          Cluster: CORTEX • TITAN • SPECTRA • GUARDIAN
        </span>
        
        {/* Task telemetry */}
        <div className="flex items-center gap-1.5 mt-0.5 min-w-0">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_6px_#10b981] shrink-0" />
          <span className="text-[6.5px] text-slate-400 font-mono truncate leading-none">
            {task}
          </span>
        </div>
        
        {/* Telemetry metrics bar */}
        <div className="flex justify-between items-center text-[5.5px] font-mono text-purple-400/80 mt-1 uppercase">
          <span>THOUGHT_DEPTH: {thoughtDepth}%</span>
          <span>SYS_LINK: SECURE</span>
        </div>
      </div>
    </div>
  );
};

export default AgentCard;
