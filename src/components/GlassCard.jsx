import React from 'react';
import { motion } from 'framer-motion';

const GlassCard = ({ children, title, className = "", isPurple = false }) => {
  // Exact styling guidelines from user
  // backdrop-filter: blur(18px);
  // border: 1px solid rgba(0,229,255,.25);
  // box-shadow: 0 0 20px rgba(0,229,255,.15), 0 0 50px rgba(138,43,226,.15);
  
  const borderStyles = isPurple 
    ? {
        border: '1px solid rgba(138,43,226,0.3)',
        boxShadow: '0 0 25px rgba(138,43,226,0.15), 0 0 60px rgba(112,0,255,0.12), inset 0 0 12px rgba(138,43,226,0.05)',
      }
    : {
        border: '1px solid rgba(0,229,255,0.28)',
        boxShadow: '0 0 20px rgba(0,229,255,0.15), 0 0 50px rgba(138,43,226,0.15), inset 0 0 12px rgba(0,229,255,0.04)',
      };

  const cornerColor = isPurple ? 'border-purple-500' : 'border-cyan-400';
  const accentColor = isPurple ? 'bg-purple-500' : 'bg-cyan-400';

  return (
    <motion.div
      whileHover={{ 
        scale: 1.02, 
        y: -1.5,
        boxShadow: isPurple
          ? '0 0 35px rgba(138,43,226,0.32), 0 0 70px rgba(112,0,255,0.25), inset 0 0 15px rgba(138,43,226,0.08)'
          : '0 0 30px rgba(0,229,255,0.3), 0 0 60px rgba(138,43,226,0.28), inset 0 0 15px rgba(0,229,255,0.08)',
        borderColor: isPurple ? 'rgba(138,43,226,0.45)' : 'rgba(0,229,255,0.45)'
      }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      style={borderStyles}
      className={`relative rounded-md bg-[#020611]/80 backdrop-blur-[18px] p-3 overflow-hidden transition-all duration-300 ${className}`}
    >
      {/* Top linear glow sheen */}
      <div className={`absolute top-0 left-0 right-0 h-[1.2px] bg-gradient-to-r from-transparent ${isPurple ? 'via-purple-500/40' : 'via-cyan-400/40'} to-transparent`} />

      {/* Cybernetic HUD Corner brackets */}
      <div className={`absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-top-left-radius-[3px] ${cornerColor}`} />
      <div className={`absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-top-right-radius-[3px] ${cornerColor}`} />
      <div className={`absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-bottom-left-radius-[3px] ${cornerColor}`} />
      <div className={`absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-bottom-right-radius-[3px] ${cornerColor}`} />

      {/* HUD Accent lines at the edges */}
      <div className={`absolute top-2 left-0 w-[2px] h-3 ${accentColor} opacity-40`} />
      <div className={`absolute top-2 right-0 w-[2px] h-3 ${accentColor} opacity-40`} />

      {/* Optional Card Title Header */}
      {title && (
        <div className="mb-2.5 border-b border-white/5 pb-1 flex justify-between items-center relative">
          <span className={`text-[8.5px] font-black uppercase tracking-[0.2em] font-mono ${isPurple ? 'text-purple-400' : 'text-cyan-400'}`}>
            {title}
          </span>
          <div className="flex gap-1">
            <span className={`w-1 h-[2px] ${accentColor} opacity-40`} />
            <span className={`w-3 h-[2px] ${accentColor} opacity-40`} />
          </div>
          <div className={`absolute bottom-0 left-0 h-[1.2px] w-8 ${isPurple ? 'bg-purple-500 shadow-[0_0_8px_#8a2be2]' : 'bg-cyan-400 shadow-[0_0_8px_#00e5ff]'}`} />
        </div>
      )}

      {/* Card Content */}
      <div className="relative z-10 w-full h-full min-h-0">
        {children}
      </div>
    </motion.div>
  );
};

export default GlassCard;
