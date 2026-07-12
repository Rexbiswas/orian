import React from 'react';
import { motion } from 'framer-motion';
import GlassCard from './GlassCard';

const LiveOutput = ({ aiOutput }) => {
  return (
    <GlassCard title="LIVE AI OUTPUT" className="w-[28%] flex p-3 flex-col justify-center overflow-hidden">
      <div className="flex-1 bg-black/40 border border-white/5 rounded p-2 flex items-center justify-between overflow-hidden">
        <p className="text-[8.5px] text-slate-400 font-medium font-mono leading-snug pr-2 truncate">
          {aiOutput || 'AI is ready and listening...'}
        </p>

        {/* 4 Pulsating loading dots on the far right */}
        <div className="flex gap-1.5 shrink-0 pr-1">
          {Array.from({ length: 4 }).map((_, i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff]"
              animate={{ opacity: [0.2, 1.0, 0.2] }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.25,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </div>
    </GlassCard>
  );
};

export default LiveOutput;
