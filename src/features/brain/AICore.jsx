import React from 'react';
import GlassCard from '../ui/GlassCard';
import CircularCore from './CircularCore';
import AIModeCards from '../modes/AIModeCards';

const AICore = ({ emotion, isSpeaking, isListening, audioLevel }) => {
  return (
    <GlassCard isPurple={true} className="h-[400px] lg:h-auto lg:flex-1 flex flex-col p-4 justify-between items-center relative overflow-hidden border border-purple-500/25 shadow-[0_0_20px_rgba(138,43,226,0.15)]">
      
      {/* Top Left Twin Glowing Dots */}
      
      <div className="absolute top-4 left-4 flex gap-1.5 z-20">
        <span className="w-2.5 h-2.5 rounded-full bg-[#00E5FF] shadow-[0_0_12px_rgba(0,229,255,0.9)] animate-pulse" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6] shadow-[0_0_12px_rgba(59,130,246,0.9)] animate-pulse" style={{ animationDelay: '0.4s' }} />
      </div>

      {/* Cybernetic Centered Title Header */}
      <div className="w-full flex justify-center mt-1 relative z-10">
        <div className="relative border border-cyan-500/30 px-8 py-1.5 bg-[#030712]/90 backdrop-blur rounded-[2px] shadow-[inset_0_0_12px_rgba(0,229,255,0.18)] flex items-center justify-center min-w-[200px]">
          {/* Sci-Fi HUD Corner brackets */}
          <div className="absolute -top-[1px] -left-[1px] w-1.5 h-1.5 border-t-2 border-l-2 border-cyan-400" />
          <div className="absolute -top-[1px] -right-[1px] w-1.5 h-1.5 border-t-2 border-r-2 border-cyan-400" />
          <div className="absolute -bottom-[1px] -left-[1px] w-1.5 h-1.5 border-b-2 border-l-2 border-cyan-400" />
          <div className="absolute -bottom-[1px] -right-[1px] w-1.5 h-1.5 border-b-2 border-r-2 border-cyan-400" />
          
          <span className="text-[10px] font-black text-cyan-300 tracking-[0.2em] uppercase select-none font-sans">
            AI Core - Neural Engine
          </span>
        </div>
      </div>

      {/* 3D particle core canvas wrapper */}
      <div className="flex-1 w-full flex items-center justify-center min-h-0 py-0.5">
        <CircularCore 
          emotion={emotion} 
          isSpeaking={isSpeaking} 
          isListening={isListening}
          audioLevel={audioLevel} 
        />
      </div>

      {/* 4 Mode settings badges */}
      <AIModeCards />
    </GlassCard>
  );
};

export default AICore;
