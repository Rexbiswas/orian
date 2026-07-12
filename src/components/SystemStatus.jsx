import React from 'react';
import GlassCard from './GlassCard';

const SystemStatus = () => {
  const services = [
    { name: "Voice Assistant", val: "ONLINE", ok: true },
    { name: "Speech Recognition", val: "ACTIVE", ok: true },
    { name: "Web Agent", val: "ACTIVE", ok: true },
    { name: "Vision Engine (YOLO)", val: "ACTIVE", ok: true },
    { name: "Database", val: "CONNECTED", ok: true },
    { name: "Security Layer", val: "ENCRYPTED", ok: true }
  ];

  return (
    <GlassCard title="System Status" className="flex-1 flex flex-col min-h-0">
      <div className="flex-1 flex flex-col justify-around pr-1 overflow-hidden font-mono text-[8px] my-1 pt-1 min-h-0">
        {services.map(service => (
          <div key={service.name} className="flex items-center justify-between border-b border-white/[0.02] pb-0.5 last:border-none">
            <span className="text-slate-400 font-medium">{service.name}</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-1 h-1 rounded-full ${service.ok ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-red-500'} animate-pulse`} />
              <span className={`font-black tracking-widest text-[7px] ${service.ok ? 'text-emerald-400' : 'text-red-500'}`}>
                {service.val}
              </span>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
};

export default SystemStatus;
