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
        { stroke: 'rgba(0, 229, 255, 0.55)', a: amp, f: freq, speed: 0.05 },
        { stroke: 'rgba(176, 38, 255, 0.4)', a: amp * 0.7, f: freq * 0.8, speed: -0.07 },
        { stroke: 'rgba(0, 229, 255, 0.18)', a: amp * 1.3, f: freq * 0.5, speed: 0.03 }
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

const VoiceInput = ({ isSpeaking, audioLevel, isListening, toggleListening }) => {
  return (
    <GlassCard title="VOICE INPUT" className="w-full lg:w-[28%] flex p-3 items-center overflow-hidden">
      {/* Waveform Column on the Left */}
      <div className="flex-1 flex flex-col h-full justify-between overflow-hidden mr-2">
        <div className="h-7 w-full">
          <VoiceWaveform isSpeaking={isSpeaking} audioLevel={audioLevel} isListening={isListening} />
        </div>
        <span className="text-[7px] text-purple-400 font-mono tracking-wider mt-1.5 leading-none">
          {isListening ? "Listening..." : "Listening Standby"}
        </span>
      </div>

      {/* Large Microphone button on the Right */}
      <button 
        onClick={toggleListening}
        className={`w-12 h-12 rounded-full flex items-center justify-center transition-all shrink-0 ${
          isListening 
          ? 'bg-purple-600/35 border-2 border-purple-500 text-purple-200 shadow-[0_0_20px_rgba(176,38,255,0.7)] animate-pulse'
          : 'bg-black/40 border border-purple-500/30 text-purple-400 hover:text-purple-200 hover:bg-purple-500/10 hover:shadow-[0_0_15px_rgba(138,43,226,0.4)]'
        }`}
      >
        {isListening ? <MicOff size={18} className="animate-pulse" /> : <Mic size={18} />}
      </button>
    </GlassCard>
  );
};

export default VoiceInput;
