import React from 'react';
import { motion } from 'framer-motion';

const HUDSkeleton = ({ title = "CORE LINK LOADING", className = "", isPurple = false, height = "200px" }) => {
  const cornerColor = isPurple ? 'border-purple-500' : 'border-cyan-400';
  const accentColor = isPurple ? 'bg-purple-500' : 'bg-cyan-400';
  const textColor = isPurple ? 'text-purple-400' : 'text-cyan-400';
  const shadowColor = isPurple ? 'rgba(138,43,226,0.15)' : 'rgba(0,229,255,0.15)';

  const borderStyles = isPurple 
    ? {
        border: '1px solid rgba(138,43,226,0.2)',
        boxShadow: `0 0 20px ${shadowColor}, inset 0 0 10px rgba(138,43,226,0.03)`,
      }
    : {
        border: '1px solid rgba(0,229,255,0.2)',
        boxShadow: `0 0 20px ${shadowColor}, inset 0 0 10px rgba(0,229,255,0.03)`,
      };

  return (
    <div
      style={{ ...borderStyles, height }}
      className={`relative rounded-md bg-[#020611]/60 backdrop-blur-[12px] p-3 overflow-hidden flex flex-col justify-between ${className}`}
    >
      {/* Laser line scanner animation */}
      <motion.div 
        animate={{ y: ['0%', '1000%', '0%'] }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        className={`absolute left-0 right-0 h-[1.5px] ${isPurple ? 'bg-gradient-to-r from-transparent via-purple-500 to-transparent shadow-[0_0_8px_#8a2be2]' : 'bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_8px_#00e5ff]'} opacity-40`}
      />

      {/* Cybernetic HUD Corner brackets */}
      <div className={`absolute top-0 left-0 w-2.5 h-2.5 border-t border-l ${cornerColor}`} />
      <div className={`absolute top-0 right-0 w-2.5 h-2.5 border-t border-r ${cornerColor}`} />
      <div className={`absolute bottom-0 left-0 w-2.5 h-2.5 border-b border-l ${cornerColor}`} />
      <div className={`absolute bottom-0 right-0 w-2.5 h-2.5 border-b border-r ${cornerColor}`} />

      {/* Title block */}
      <div className="mb-2 border-b border-white/5 pb-1 flex justify-between items-center relative">
        <span className={`text-[8px] font-black uppercase tracking-[0.2em] font-mono ${textColor} animate-pulse`}>
          {title}
        </span>
        <div className="flex gap-1">
          <span className={`w-1 h-[2px] ${accentColor} opacity-40 animate-pulse`} />
          <span className={`w-2.5 h-[2px] ${accentColor} opacity-40 animate-pulse`} />
        </div>
        <div className={`absolute bottom-0 left-0 h-[1px] w-6 ${isPurple ? 'bg-purple-500 shadow-[0_0_6px_#8a2be2]' : 'bg-cyan-400 shadow-[0_0_6px_#00e5ff]'}`} />
      </div>

      {/* Main Skeleton Layout */}
      <div className="flex-1 flex flex-col justify-between gap-2.5 pt-1.5 pb-0.5">
        {/* Mock Graphic Indicator */}
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-full border border-white/10 flex items-center justify-center shrink-0 overflow-hidden bg-white/[0.02]">
            <div className={`w-6 h-6 rounded-full border border-dashed ${isPurple ? 'border-purple-500/30' : 'border-cyan-400/30'} animate-spin`} style={{ animationDuration: '6s' }} />
            <div className={`absolute inset-0 bg-gradient-to-tr ${isPurple ? 'from-purple-500/10 to-transparent' : 'from-cyan-400/10 to-transparent'} animate-pulse`} />
          </div>
          
          <div className="flex-1 flex flex-col gap-1.5">
            <div className="h-2 w-3/4 rounded bg-white/5 overflow-hidden relative">
              <motion.div 
                animate={{ x: ['-100%', '100%'] }} 
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }} 
                className={`absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent ${isPurple ? 'via-purple-500/20' : 'via-cyan-400/20'} to-transparent`}
              />
            </div>
            <div className="h-1.5 w-1/2 rounded bg-white/5 overflow-hidden relative">
              <motion.div 
                animate={{ x: ['-100%', '100%'] }} 
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }} 
                className={`absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent ${isPurple ? 'via-purple-500/20' : 'via-cyan-400/20'} to-transparent`}
              />
            </div>
          </div>
        </div>

        {/* Telemetry Rows */}
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex justify-between items-center text-[7px] font-mono text-slate-500">
              <div className="flex items-center gap-1.5">
                <span className={`w-1 h-1 rounded-full ${accentColor} opacity-50`} />
                <div className="h-2 w-16 rounded bg-white/5 overflow-hidden relative">
                  <motion.div 
                    animate={{ x: ['-100%', '100%'] }} 
                    transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut", delay: i * 0.15 }} 
                    className={`absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent ${isPurple ? 'via-purple-500/15' : 'via-cyan-400/15'} to-transparent`}
                  />
                </div>
              </div>
              <div className="h-2 w-8 rounded bg-white/5 overflow-hidden relative">
                <motion.div 
                  animate={{ x: ['-100%', '100%'] }} 
                  transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut", delay: i * 0.2 }} 
                  className={`absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent ${isPurple ? 'via-purple-500/15' : 'via-cyan-400/15'} to-transparent`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cyberpunk Footer Stats Bar */}
      <div className="mt-1 pt-1 border-t border-white/5 flex justify-between items-center text-[6px] text-slate-600 font-mono tracking-tighter">
        <span>LINKING SIGNAL...</span>
        <span>LATENCY: -- MS</span>
      </div>
    </div>
  );
};

export default HUDSkeleton;
