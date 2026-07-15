import React from 'react';
import GlassCard from './GlassCard';
import HumanSenses from './HumanSenses/HumanSenses';
import { Smile, Target, BrainCircuit, BatteryLow, ShieldAlert, Cpu, Meh, Flame, Sparkles } from 'lucide-react';

const EmotionDetection = ({ currentSenses, handleSenseUpdate }) => {
  // Helpers to simulate live data or pull parsed data
  const getEmotionPercent = (emoName, currentEmo, currentBase) => {
    if (currentBase === emoName.toLowerCase()) {
      const match = currentEmo.match(/\[(\d+)%\]/);
      return match ? parseInt(match[1]) : 85;
    }
    const bases = { happy: 22, focused: 15, neutral: 12, thinking: 18, tired: 8, stress: 5 };
    const base = bases[emoName.toLowerCase()] || 10;
    return Math.round(base + (Math.sin(Date.now() / 2000 + emoName.length) * 3));
  };

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
    <GlassCard title="Emotion Detection" className="h-[280px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div className="flex-1 flex gap-3 overflow-hidden min-h-0 pt-1">
        {/* Webcam Viewport */}
        <div className="w-[55%] h-full">
          <HumanSenses onSenseUpdate={handleSenseUpdate} />
        </div>

        {/* Stats and Progress Meters */}
        <div className="w-[45%] flex flex-col justify-between overflow-hidden">
          <div className="bg-white/2 border border-white/5 rounded p-1.5 flex flex-col items-center">
            <span className="text-[6px] font-black text-slate-500 uppercase tracking-wider mb-1 block">Current Emotion</span>
            <div className="flex items-center gap-1.5">
              {getEmotionIcon(currentSenses.base)}
              <span className="text-[9px] font-black text-white capitalize leading-none">
                {currentSenses.base || 'neutral'}
              </span>
            </div>
          </div>

          {/* Progress meters */}
          <div className="flex-1 flex flex-col justify-around my-1 overflow-hidden">
            {['Happy', 'Focused', 'Neutral', 'Thinking', 'Tired', 'Stress'].map(emo => {
              const val = getEmotionPercent(emo, currentSenses.emotion, currentSenses.base);
              const isActive = (currentSenses.base || 'neutral') === emo.toLowerCase();
              return (
                <div key={emo} className="flex flex-col gap-0.5">
                  <div className="flex justify-between text-[6.5px] font-black uppercase">
                    <span className={isActive ? "text-cyan-400" : "text-slate-500"}>{emo}</span>
                    <span className={isActive ? "text-cyan-400" : "text-slate-400"}>{val}%</span>
                  </div>
                  <div className="h-[3px] bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${isActive ? 'bg-cyan-400 shadow-[0_0_8px_#00e5ff]' : 'bg-cyan-400/20'}`}
                      style={{ width: `${val}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default EmotionDetection;
