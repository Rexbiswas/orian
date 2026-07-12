import React, { useRef, useEffect } from 'react';
import GlassCard from './GlassCard';

const MemoryTimeline = ({ logs }) => {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom on log additions
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <GlassCard title="Memory Timeline" className="flex-1 flex flex-col min-h-0">
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-2 pr-1 no-scrollbar font-mono text-[8px] pt-1"
      >
        {logs.slice(0, 7).map((log, idx) => (
          <div key={log.id || idx} className="flex gap-2.5 items-start border-l border-white/10 pl-2 py-0.5 hover:bg-white/2 transition-colors">
            <span className="text-purple-400 font-bold shrink-0">{log.timestamp}</span>
            <div className="flex flex-col gap-0.5">
              <span className="text-white font-medium leading-tight">{log.message.replace(/_/g, ' ')}</span>
              <span className="text-[5.5px] text-slate-500 uppercase font-black">TYPE: {log.type} // {log.status}</span>
            </div>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-center text-slate-600 pt-6">Memory buffer empty</div>
        )}
      </div>
    </GlassCard>
  );
};

export default MemoryTimeline;
