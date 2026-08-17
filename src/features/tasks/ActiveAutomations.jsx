import React from 'react';
import GlassCard from '../ui/GlassCard';
import ProgressBar from '../ui/ProgressBar';

const ActiveAutomations = () => {
  const automations = [
    { name: "Web Search Automation", val: 75, status: "Running", color: "bg-cyan-400" },
    { name: "Email Draft Generator", val: 60, status: "Running", color: "bg-cyan-400" },
    { name: "File Organizer", val: 100, status: "Completed", color: "bg-emerald-400" },
    { name: "AI Meeting Assistant", val: 0, status: "Idle", color: "bg-slate-700" },
    { name: "Data Extractor", val: 40, status: "Running", color: "bg-cyan-400" }
  ];

  return (
    <GlassCard title="Active Automations" className="h-[200px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div className="flex-1 flex flex-col justify-around overflow-hidden my-1 pt-1 min-h-0">
        {automations.map(task => (
          <ProgressBar 
            key={task.name} 
            label={task.name} 
            value={task.val} 
            isPurple={task.status === 'Running' ? false : (task.status === 'Completed' ? false : true)} 
            status={task.status} 
          />
        ))}
      </div>
    </GlassCard>
  );
};

export default ActiveAutomations;
