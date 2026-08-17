import React from 'react';
import { useVoice } from '../../context/VoiceContext';
import GlassCard from '../ui/GlassCard';
import CircularCore from './CircularCore';

const NeuralSchema = ({ emotion = 'neutral' }) => {
  const { isSpeaking, audioLevel } = useVoice();

  return (
    <GlassCard isPurple={true} className="w-full max-w-[420px] h-[400px] flex flex-col p-4 justify-between items-center relative overflow-hidden border border-purple-500/25 shadow-[0_0_20px_rgba(138,43,226,0.15)]">
      
      {/* Top Left Twin Glowing Dots */}
      <div className="absolute top-4 left-4 flex gap-1.5 z-20">
        <span className="w-2.5 h-2.5 rounded-full bg-[#00E5FF] shadow-[0_0_12px_rgba(0,229,255,0.9)] animate-pulse" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6] shadow-[0_0_12px_rgba(59,130,246,0.9)] animate-pulse" style={{ animationDelay: '0.4s' }} />
      </div>


      {/* 3D particle core canvas wrapper */}
      <div className="flex-1 w-full flex items-center justify-center min-h-0 py-0.5">
        <CircularCore 
          emotion={emotion} 
          isSpeaking={isSpeaking} 
          audioLevel={audioLevel} 
        />
      </div>
    </GlassCard>
  );
};

export default NeuralSchema;
