import React from 'react';
import { motion } from 'framer-motion';
import { playHoverClick } from '../../utils/sound';

const GlassCard = ({ children, title, className = "", isPurple = false }) => {
  const borderStyles = isPurple
    ? {
        border: '1px solid rgba(0,255,136,0.28)',
        boxShadow: '0 0 28px rgba(0,255,136,0.1), 0 0 55px rgba(0,200,100,0.08), inset 0 1px 0 rgba(0,255,136,0.08)',
      }
    : {
        border: '1px solid rgba(0,102,255,0.28)',
        boxShadow: '0 0 24px rgba(0,102,255,0.12), 0 0 55px rgba(0,50,200,0.1), inset 0 1px 0 rgba(0,102,255,0.08)',
      };

  const accentHex   = isPurple ? '#00FF88' : '#0066FF';
  const cornerColor = isPurple ? 'border-green-400/60' : 'border-blue-500/60';
  const ledColor    = isPurple ? 'bg-green-400' : 'bg-blue-500';
  const titleColor  = isPurple ? 'text-green-400' : 'text-blue-400';
  const sheenVia    = isPurple ? 'via-green-400/25' : 'via-blue-500/25';

  return (
    <motion.div
      onMouseEnter={() => playHoverClick()}
      whileHover={{
        scale: 1.012,
        y: -1,
        boxShadow: isPurple
          ? '0 0 38px rgba(0,255,136,0.22), 0 0 80px rgba(0,200,100,0.15), inset 0 1px 0 rgba(0,255,136,0.12)'
          : '0 0 34px rgba(0,102,255,0.28), 0 0 70px rgba(0,50,200,0.18), inset 0 1px 0 rgba(0,102,255,0.14)',
      }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      style={borderStyles}
      className={`relative rounded-[14px] bg-[#03060F]/80 backdrop-blur-[22px] p-3 overflow-hidden transition-all duration-300 ${className}`}
    >
      {/* Top sheen line */}
      <div className={`absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent ${sheenVia} to-transparent pointer-events-none`} />

      {/* Ambient inner radial glow */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{ background: `radial-gradient(ellipse at 50% 0%, ${accentHex}22 0%, transparent 70%)` }}
      />

      {/* Corner bracket accents */}
      <div className={`absolute top-0 left-0 w-3 h-3 border-t-[1.5px] border-l-[1.5px] rounded-tl-[14px] ${cornerColor}`} />
      <div className={`absolute top-0 right-0 w-3 h-3 border-t-[1.5px] border-r-[1.5px] rounded-tr-[14px] ${cornerColor}`} />
      <div className={`absolute bottom-0 left-0 w-3 h-3 border-b-[1.5px] border-l-[1.5px] rounded-bl-[14px] ${cornerColor}`} />
      <div className={`absolute bottom-0 right-0 w-3 h-3 border-b-[1.5px] border-r-[1.5px] rounded-br-[14px] ${cornerColor}`} />

      {/* Card Title Header */}
      {title && (
        <div className="mb-2 pb-1.5 flex items-center justify-between relative border-b border-white/[0.04]">
          <div className="flex items-center gap-2">
            <span className={`w-1 h-1 rounded-full ${ledColor} shadow-[0_0_5px_currentColor] animate-pulse shrink-0`} />
            <span className={`text-[8px] font-black uppercase tracking-[0.22em] font-mono ${titleColor}`}>
              {title}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className={`w-4 h-[1.5px] ${ledColor} opacity-30 rounded-full`} />
            <span className={`w-1.5 h-[1.5px] ${ledColor} opacity-50 rounded-full`} />
          </div>
          <div
            className="absolute bottom-0 left-0 h-[1px] w-10 opacity-60"
            style={{ background: `linear-gradient(to right, ${accentHex}, transparent)`, boxShadow: `0 0 6px ${accentHex}` }}
          />
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
