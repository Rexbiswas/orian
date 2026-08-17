import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Terminal } from 'lucide-react';
import GlassCard from './GlassCard';

const LiveOutput = ({ aiOutput }) => {
  const isAgentOnlineMessage = aiOutput && aiOutput.toLowerCase().includes('online');

  return (
    <GlassCard title="LIVE AI OUTPUT" className="w-full lg:w-[28%] flex p-3 flex-col justify-center overflow-hidden">
      <div
        className={`flex-1 relative rounded-lg overflow-hidden transition-all duration-300 ${
          isAgentOnlineMessage
            ? 'bg-cyan-950/25 border border-cyan-400/40 shadow-[0_0_15px_rgba(0,229,255,0.15),inset_0_0_10px_rgba(0,229,255,0.08)]'
            : 'bg-blue-950/15 border border-blue-500/20 shadow-[inset_0_0_12px_rgba(0,102,255,0.05)]'
        }`}
      >
        {/* Shimmer sweep */}
        <div className="absolute inset-0 pointer-events-none animate-shimmer opacity-60" />
        
        <div className="relative z-10 p-2.5 flex items-center justify-between gap-2 h-full">
          <AnimatePresence mode="wait">
            <motion.p
              key={aiOutput || 'default'}
              initial={{ opacity: 0, y: 3 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -3 }}
              transition={{ duration: 0.18 }}
              className={`text-[8.5px] font-mono font-medium leading-relaxed flex-1 overflow-hidden select-text ${
                isAgentOnlineMessage
                  ? 'text-cyan-200 drop-shadow-[0_0_6px_rgba(0,229,255,0.5)]'
                  : 'text-blue-100/90'
              }`}
            >
              <span className="text-cyan-400 mr-1.5 font-bold">▶</span>
              <span className={isAgentOnlineMessage ? "capitalize font-bold tracking-wider" : ""}>
                {aiOutput || 'Orian is ready. Awaiting command...'}
              </span>
            </motion.p>
          </AnimatePresence>

          <div className="flex flex-col gap-1 shrink-0 items-center justify-center">
            {isAgentOnlineMessage ? (
              <Sparkles size={13} className="text-cyan-400 animate-pulse" />
            ) : (
              Array.from({ length: 3 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff]"
                  animate={{ opacity: [0.2, 1.0, 0.2], scale: [0.8, 1.15, 0.8] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.25, ease: 'easeInOut' }}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default LiveOutput;
