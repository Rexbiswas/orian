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
    <GlassCard title="Memory Timeline" className="h-[200px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-1.5 pr-1 no-scrollbar font-mono text-[8px] pt-1 relative"
      >
        {/* Full vertical timeline track */}
        <div className="absolute left-[5px] top-0 bottom-0 w-[1px] bg-purple-500/15" />

        {logs.slice(0, 7).map((log, idx) => (
          <div key={log.id || idx} className="flex gap-3 items-center relative pl-3.5 py-1 hover:bg-white/2 transition-colors min-w-0">
            {/* Timeline dot */}
            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_#a855f7] z-10 shrink-0 absolute left-[2px]" />

            <span className="text-[7.5px] text-purple-400 font-bold tracking-wider shrink-0 w-[48px] pl-2 font-mono">
              {log.timestamp}
            </span>
            <span className="text-[7.5px] text-slate-200 font-medium tracking-wide truncate leading-tight min-w-0 flex-1">
              {log.message.replace(/_/g, ' ')}
            </span>
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
