import React from 'react';
import { motion } from 'framer-motion';
import GlassCard from './GlassCard';

const LiveOutput = ({ aiOutput }) => {
  return (
    <GlassCard title="LIVE AI OUTPUT" className="w-full lg:w-[28%] flex p-3 flex-col justify-center overflow-hidden">
      <div className="flex-1 relative rounded-lg overflow-hidden" style={{
        background: 'rgba(0,102,255,0.025)',
        border: '1px solid rgba(0,102,255,0.15)',
        boxShadow: 'inset 0 0 12px rgba(0,102,255,0.05)'
      }}>
        {/* Shimmer sweep */}
        <div className="absolute inset-0 pointer-events-none animate-shimmer opacity-60" />
        <div className="relative z-10 p-2 flex items-start justify-between gap-2 h-full">
          <p className="text-[8px] text-blue-100/80 font-medium font-mono leading-relaxed flex-1 overflow-hidden">
            <span className="text-blue-400/60 mr-1">▶</span>
            {aiOutput || 'Orian is ready. Awaiting command...'}
          </p>
          <div className="flex flex-col gap-1 pt-0.5 shrink-0">
            {Array.from({ length: 3 }).map((_, i) => (
              <motion.div
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_6px_#0066FF]"
                animate={{ opacity: [0.15, 1.0, 0.15], scale: [0.8, 1.1, 0.8] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.3, ease: 'easeInOut' }}
              />
            ))}
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default LiveOutput;
