import React, { useRef, useEffect } from 'react';
import GlassCard from '../ui/GlassCard';

const MemoryTimeline = ({ logs = [] }) => {
  const scrollRef = useRef(null);

  // Default timeline logs to populate if logs are empty, matching user design specs
  const defaultLogs = [
    { timestamp: "11:40 PM", message: "Learned new automation workflow", id: "d1" },
    { timestamp: "11:30 PM", message: "Completed web search task", id: "d2" },
    { timestamp: "11:20 PM", message: "Updated local knowledge base", id: "d3" },
    { timestamp: "11:15 PM", message: "Eevolution metrics fine-tuned", id: "d4" },
    { timestamp: "11:10 PM", message: "System booted successfully", id: "d5" }
  ];

  const activeLogs = logs.length > 0 ? logs : defaultLogs;

  // Auto-scroll to bottom on log additions
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeLogs]);

  return (
    <GlassCard title="Memory Timeline" className="h-[200px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-1.5 pr-1 no-scrollbar font-mono text-[8px] pt-1 relative"
      >
        {/* Full vertical timeline track */}
        <div className="absolute left-[5px] top-0 bottom-0 w-[1px] bg-blue-500/15" />

        {activeLogs.slice(0, 5).map((log, idx) => (
          <div key={log.id || idx} className="flex gap-3 items-center relative pl-3.5 py-1 hover:bg-white/2 transition-colors min-w-0">
            {/* Timeline dot */}
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_#0066FF] z-10 shrink-0 absolute left-[2px]" />

            <span className="text-[7.5px] text-blue-400 font-bold tracking-wider shrink-0 w-[48px] pl-2 font-mono">
              {log.timestamp}
            </span>
            <span className="text-[7.5px] text-slate-200 font-medium tracking-wide truncate leading-tight min-w-0 flex-1">
              {log.message.replace(/_/g, ' ')}
            </span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
};

export default MemoryTimeline;
