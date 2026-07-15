import React from 'react';
import GlassCard from './GlassCard';

const BrainDevelopment = ({ evolution = "68.4%" }) => {
  return (
    <GlassCard title="Brain Development" className="h-[220px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div className="flex-1 flex gap-3 overflow-hidden items-center pt-1">
        {/* Wireframe Brain SVG */}
        <div className="w-[45%] h-full relative flex items-center justify-center">
          <svg className="w-full h-[95%] text-purple-500/50 filter drop-shadow-[0_0_12px_rgba(138,43,226,0.5)]" viewBox="0 0 100 100">
            {/* Left Hemisphere */}
            <path d="M50 15 C30 15, 20 28, 20 50 C20 72, 32 82, 50 85 C42 75, 45 60, 50 50 Z" fill="none" stroke="currentColor" strokeWidth="0.95" />
            <path d="M50 25 C38 25, 28 32, 28 50 C28 65, 38 75, 50 78" fill="none" stroke="currentColor" strokeWidth="0.4" strokeDasharray="3 3" />
            <path d="M50 35 C42 35, 35 40, 35 50 C35 58, 42 65, 50 68" fill="none" stroke="currentColor" strokeWidth="0.25" opacity="0.5" />
            
            {/* Right Hemisphere */}
            <path d="M50 15 C70 15, 80 28, 80 50 C80 72, 68 82, 50 85 C58 75, 55 60, 50 50 Z" fill="none" stroke="currentColor" strokeWidth="0.95" />
            <path d="M50 25 C62 25, 72 32, 72 50 C72 65, 62 75, 50 78" fill="none" stroke="currentColor" strokeWidth="0.4" strokeDasharray="3 3" />
            <path d="M50 35 C58 35, 65 40, 65 50 C65 58, 58 65, 50 68" fill="none" stroke="currentColor" strokeWidth="0.25" opacity="0.5" />

            {/* Concentric neural rings */}
            <circle cx="50" cy="50" r="12" fill="none" stroke="#a855f7" strokeWidth="0.25" strokeDasharray="1 4" opacity="0.4" className="animate-spin-slow" />
            <circle cx="50" cy="50" r="24" fill="none" stroke="#00e5ff" strokeWidth="0.25" strokeDasharray="2 6" opacity="0.25" />

            {/* Pulses / Nodes */}
            <circle cx="50" cy="15" r="1.5" fill="#a855f7" className="animate-ping" />
            <circle cx="20" cy="50" r="1" fill="#00e5ff" />
            <circle cx="80" cy="50" r="1" fill="#00e5ff" />
            <circle cx="50" cy="85" r="1.5" fill="#a855f7" />
            <circle cx="34" cy="36" r="1" fill="#fff" />
            <circle cx="66" cy="36" r="1" fill="#fff" />
            <circle cx="32" cy="62" r="1" fill="#a855f7" />
            <circle cx="68" cy="62" r="1" fill="#a855f7" />
            <circle cx="50" cy="50" r="2.2" fill="#fff" className="animate-pulse" />
            <circle cx="40" cy="28" r="0.8" fill="#a855f7" />
            <circle cx="60" cy="28" r="0.8" fill="#a855f7" />
            <circle cx="45" cy="72" r="0.8" fill="#a855f7" />
            <circle cx="55" cy="72" r="0.8" fill="#a855f7" />
            <circle cx="28" cy="42" r="0.8" fill="#00e5ff" />
            <circle cx="72" cy="42" r="0.8" fill="#00e5ff" />

            {/* Axons & Connection Lines */}
            <line x1="34" y1="36" x2="50" y2="50" stroke="#fff" strokeWidth="0.25" opacity="0.4" />
            <line x1="66" y1="36" x2="50" y2="50" stroke="#fff" strokeWidth="0.25" opacity="0.4" />
            <line x1="32" y1="62" x2="50" y2="50" stroke="#a855f7" strokeWidth="0.25" opacity="0.4" />
            <line x1="68" y1="62" x2="50" y2="50" stroke="#a855f7" strokeWidth="0.25" opacity="0.4" />
            <line x1="20" y1="50" x2="34" y2="36" stroke="#00e5ff" strokeWidth="0.2" opacity="0.35" />
            <line x1="80" y1="50" x2="66" y2="36" stroke="#00e5ff" strokeWidth="0.2" opacity="0.35" />
            <line x1="20" y1="50" x2="32" y2="62" stroke="#00e5ff" strokeWidth="0.2" opacity="0.35" />
            <line x1="80" y1="50" x2="68" y2="62" stroke="#00e5ff" strokeWidth="0.2" opacity="0.35" />
            <line x1="50" y1="15" x2="34" y2="36" stroke="#a855f7" strokeWidth="0.2" opacity="0.35" />
            <line x1="50" y1="15" x2="66" y2="36" stroke="#a855f7" strokeWidth="0.2" opacity="0.35" />
            <line x1="50" y1="85" x2="32" y2="62" stroke="#a855f7" strokeWidth="0.2" opacity="0.35" />
            <line x1="50" y1="85" x2="68" y2="62" stroke="#a855f7" strokeWidth="0.2" opacity="0.35" />
            <line x1="40" y1="28" x2="50" y2="50" stroke="#a855f7" strokeWidth="0.15" opacity="0.25" />
            <line x1="60" y1="28" x2="50" y2="50" stroke="#a855f7" strokeWidth="0.15" opacity="0.25" />
            <line x1="45" y1="72" x2="50" y2="50" stroke="#a855f7" strokeWidth="0.15" opacity="0.25" />
            <line x1="55" y1="72" x2="50" y2="50" stroke="#a855f7" strokeWidth="0.15" opacity="0.25" />
          </svg>
        </div>

        {/* Stats Column */}
        <div className="w-[55%] flex flex-col justify-between h-[90%] font-mono">
          <div className="flex flex-col">
            <span className="text-[6px] text-slate-500 uppercase tracking-widest font-black leading-none mb-1">Overall Intelligence</span>
            <span className="text-[12px] font-black text-purple-400 font-mono leading-none">{evolution}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[6px] text-slate-500 uppercase tracking-widest font-black leading-none mb-1">Learning Speed</span>
            <span className="text-[10px] font-bold text-white font-mono leading-none">1.8x Faster</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[6px] text-slate-500 uppercase tracking-widest font-black leading-none mb-1">Neural Connections</span>
            <span className="text-[10px] font-bold text-white font-mono leading-none">12,458</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[6px] text-slate-500 uppercase tracking-widest font-black leading-none mb-1">Knowledge Base</span>
            <span className="text-[10px] font-bold text-cyan-400 font-mono leading-none">2.7 GB</span>
          </div>
          <div className="flex items-center gap-1.5 mt-1 bg-white/2 border border-white/5 py-1 px-1.5 rounded">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]" />
            <span className="text-[6px] text-emerald-400 font-black uppercase tracking-widest leading-none">Auto Learning: ON</span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default BrainDevelopment;
