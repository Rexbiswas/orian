import React, { useRef, useEffect } from 'react';
import { Mic, MicOff } from 'lucide-react';
import GlassCard from './GlassCard';

// --- Waveform canvas visualizer ---
const VoiceWaveform = ({ isSpeaking, audioLevel, isListening }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    let animationId;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, w, h);
      ctx.lineWidth = 1.2;
      
      let amp = 2; // Flat idle line
      let freq = 0.04;
      
      if (isSpeaking) {
        amp = 14 + audioLevel * 18;
        freq = 0.08 + audioLevel * 0.06;
      } else if (isListening) {
        amp = 10 + Math.sin(Date.now() / 150) * 4;
        freq = 0.08;
      }

      phase += 0.15;

      const waves = [
        { stroke: 'rgba(0, 102, 255, 0.65)', a: amp, f: freq, speed: 0.05 },
        { stroke: 'rgba(0, 255, 136, 0.38)', a: amp * 0.7, f: freq * 0.8, speed: -0.07 },
        { stroke: 'rgba(0, 150, 255, 0.18)', a: amp * 1.3, f: freq * 0.5, speed: 0.03 }
      ];

      waves.forEach(wave => {
        ctx.strokeStyle = wave.stroke;
        ctx.beginPath();
        for (let x = 0; x < w; x++) {
          const y = h / 2 + Math.sin(x * wave.f + phase * wave.speed) * wave.a * Math.sin(x / w * Math.PI);
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      });

      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [isSpeaking, audioLevel, isListening]);

  return (
    <div className="w-full h-full relative flex items-center justify-center">
      <canvas ref={canvasRef} width="220" height="40" className="w-full h-full" />
    </div>
  );
};

import { playMicActivate, playMicDeactivate } from '../utils/sound';

const VoiceInput = ({ isSpeaking, audioLevel, isListening, toggleListening }) => {
  return (
    <GlassCard title="VOICE INPUT" className="w-full lg:w-[28%] flex p-3 items-center gap-3">

      {/* Microphone Button — LEFT side, before waveform */}
      <div className="relative shrink-0" style={{ minWidth: '44px' }}>
        {isListening && (
          <div className="absolute -inset-2 rounded-full border border-purple-500/30 animate-ping pointer-events-none" />
        )}
        <button
          onClick={() => {
            if (isListening) { playMicDeactivate(); } else { playMicActivate(); }
            toggleListening();
          }}
          className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
            isListening
              ? 'bg-blue-600/25 border-2 border-blue-500 text-blue-200 shadow-[0_0_22px_rgba(0,102,255,0.7)]'
              : 'bg-black/60 border border-blue-500/45 text-blue-400 hover:text-blue-200 hover:bg-blue-500/12 hover:shadow-[0_0_16px_rgba(0,102,255,0.5)]'
          }`}
        >
          {isListening ? <MicOff size={16} className="animate-pulse" /> : <Mic size={16} />}
        </button>
      </div>

      {/* Waveform Column — RIGHT side */}
      <div className="flex-1 flex flex-col h-full justify-between overflow-hidden">
        <div
          className="h-8 w-full rounded-md overflow-hidden relative"
          style={{
            background: 'rgba(0,229,255,0.03)',
            border: isListening ? '1px solid rgba(0,229,255,0.35)' : '1px solid rgba(255,255,255,0.05)',
            boxShadow: isListening ? '0 0 12px rgba(0,229,255,0.15)' : 'none',
            transition: 'border-color 0.4s, box-shadow 0.4s',
          }}
        >
          <VoiceWaveform isSpeaking={isSpeaking} audioLevel={audioLevel} isListening={isListening} />
        </div>
        <div className="flex items-center gap-1.5 mt-1.5">
          <span className={`w-1 h-1 rounded-full shrink-0 transition-colors duration-300 ${
            isListening ? 'bg-blue-400 shadow-[0_0_6px_#0066FF] animate-pulse' : 'bg-slate-700'
          }`} />
          <span className={`text-[7px] font-mono tracking-widest transition-colors duration-300 ${
            isListening ? 'text-blue-300' : 'text-slate-600'
          }`}>
            {isListening ? 'LISTENING ACTIVE' : 'STANDBY MODE'}
          </span>
        </div>
      </div>

    </GlassCard>
  );
};

export default VoiceInput;
