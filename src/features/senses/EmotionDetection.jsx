'use client';

import React from 'react';

import GlassCard from '../ui/GlassCard';
import HumanSenses from './HumanSenses/HumanSenses';
import { Smile, Target, BrainCircuit, BatteryLow, ShieldAlert, Cpu, Meh, Flame, Sparkles } from 'lucide-react';

const EmotionDetection = ({ currentSenses, handleSenseUpdate }) => {
  const getEmotionIcon = (base) => {
    const size = 11;
    switch (base?.toLowerCase()) {
      case 'happy': return <Smile size={size} className="text-emerald-400 drop-shadow-[0_0_5px_rgba(52,211,153,0.5)]" />;
      case 'focused': return <Target size={size} className="text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]" />;
      case 'thinking': return <BrainCircuit size={size} className="text-purple-400 drop-shadow-[0_0_5px_rgba(168,85,247,0.5)]" />;
      case 'tired': return <BatteryLow size={size} className="text-amber-500 drop-shadow-[0_0_5px_rgba(245,158,11,0.5)]" />;
      case 'stress': return <ShieldAlert size={size} className="text-red-500 drop-shadow-[0_0_5px_rgba(239,68,68,0.5)]" />;
      case 'sad': return <Meh size={size} className="text-slate-400 drop-shadow-[0_0_5px_rgba(148,163,184,0.5)]" />;
      case 'angry': return <Flame size={size} className="text-rose-500 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]" />;
      case 'surprised': return <Sparkles size={size} className="text-cyan-300 drop-shadow-[0_0_5px_rgba(103,232,249,0.5)]" />;
      default: return <Cpu size={size} className="text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]" />;
    }
  };

  return (
    <GlassCard title="Emotion Detection" className="h-[185px] lg:h-[185px] flex flex-col min-h-0 font-mono">
      <div className="flex-1 flex gap-3 overflow-hidden min-h-0 pt-0.5">
        
        {/* Webcam Viewport — locked to 4:3 to fill container perfectly with no side bars */}
        <div className="w-[54%] aspect-[4/3] shrink-0 relative">
          <HumanSenses onSenseUpdate={handleSenseUpdate} />
        </div>

        {/* Center Current Emotion Display Badge vertically */}
        <div className="w-[43%] flex flex-col justify-center overflow-hidden">
          <div className="bg-white/[0.03] border border-white/5 rounded-lg py-2 px-1.5 flex flex-col items-center shrink-0">
            <span className="text-[6px] font-black text-slate-500 uppercase tracking-widest mb-1.5 block leading-none">Current Emotion</span>
            <div className="flex items-center gap-1.5">
              {getEmotionIcon(currentSenses.base)}
              <span className="text-[9.5px] font-black text-white capitalize leading-none font-sans">
                {currentSenses.base || 'neutral'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default EmotionDetection;
