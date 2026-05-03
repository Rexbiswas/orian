import React, { useState, useEffect } from 'react';
import { motion as Motion, useMotionValue, useSpring, useTransform, AnimatePresence } from 'framer-motion';
import { useVoice } from '../context/VoiceContext';

const Ring = ({ size, duration, rotateDir = 1, opacity = 0.2, dashArray = "10 5", strokeWidth = 0.5, color = "stroke-brand-cyan" }) => (
  <Motion.svg
    width={size}
    height={size}
    viewBox="0 0 100 100"
    className="absolute pointer-events-none"
    animate={{ rotate: 360 * rotateDir }}
    transition={{ duration, repeat: Infinity, ease: "linear" }}
    style={{ opacity }}
  >
    <circle
      cx="50"
      cy="50"
      r="48"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeDasharray={dashArray}
      className={color}
    />
  </Motion.svg>
);

const DataNode = ({ radius, speed, delay, size = 2 }) => (
  <Motion.div
    className="absolute bg-brand-cyan rounded-full shadow-[0_0_8px_rgba(0,242,255,1)]"
    style={{ width: size, height: size }}
    animate={{ 
      rotate: 360 
    }}
    transition={{ 
      duration: speed, 
      repeat: Infinity, 
      ease: "linear",
      delay 
    }}
  >
    <div 
      className="absolute"
      style={{ transform: `translateY(${radius}px)` }}
    />
  </Motion.div>
);

const MicroText = ({ radius, angle, text }) => (
  <div 
    className="absolute text-[6px] font-mono text-brand-cyan/40 uppercase tracking-tighter"
    style={{ 
      transform: `rotate(${angle}deg) translateY(${radius}px)` 
    }}
  >
    {text}
  </div>
);

const NeuralSchema = ({ isLooking = false, emotion = 'neutral' }) => {
  const { isSpeaking, audioLevel } = useVoice();
  const [scanningText, setScanningText] = useState("SCANNING_FOR_USER");
  const [stabilityText, setStabilityText] = useState("STABILITY: FLOATING");
  const [telemetry, setTelemetry] = useState("0x000000");
  
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 25, stiffness: 150 };
  const rotateX = useSpring(useTransform(mouseY, [-300, 300], [15, -15]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-300, 300], [-15, 15]), springConfig);

  // Dynamic Emotion Colors
  const getEmotionColor = (type) => {
    const colors = {
      neutral: { main: 'brand-cyan', glow: 'rgba(0,242,255,1)', secondary: 'brand-purple' },
      happy: { main: 'emerald-400', glow: 'rgba(52,211,153,1)', secondary: 'brand-cyan' },
      sad: { main: 'blue-500', glow: 'rgba(59,130,246,1)', secondary: 'slate-500' },
      angry: { main: 'red-500', glow: 'rgba(239,68,68,1)', secondary: 'orange-500' },
      surprised: { main: 'yellow-400', glow: 'rgba(250,204,21,1)', secondary: 'brand-cyan' }
    };
    return colors[type] || colors.neutral;
  };

  const activeColor = getEmotionColor(emotion);

  useEffect(() => {
    const statuses = ["SCANNING_FOR_USER", "ANALYZING_ENVIRONMENT", "CALIBRATING_NEURAL_LINKS", "PROTOCOL: GENESIS", "WAITING_FOR_INPUT"];
    const stabilities = ["STABILITY: FLOATING", "STABILITY: DRIFTING", "STABILITY: DECOUPLED", "STABILITY: RE-SYNCING"];
    
    const interval = setInterval(() => {
      if (!isLooking && !isSpeaking) {
        setScanningText(statuses[Math.floor(Math.random() * statuses.length)]);
        setStabilityText(stabilities[Math.floor(Math.random() * stabilities.length)]);
        setTelemetry(`0x${Math.floor(Math.random()*16777215).toString(16).padStart(6, '0').toUpperCase()}`);
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [isLooking, isSpeaking]);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    mouseX.set(x);
    mouseY.set(y);
  };

  return (
    <div 
      className="relative flex items-center justify-center w-full h-full min-h-[500px] perspective-[1000px] overflow-visible"
      onMouseMove={handleMouseMove}
      onMouseLeave={() => { mouseX.set(0); mouseY.set(0); }}
    >
      <Motion.div 
        style={{ rotateX, rotateY }}
        animate={{ 
          scale: (isLooking ? 1.05 : 1) + (isSpeaking ? audioLevel * 0.1 : 0)
        }}
        className="relative flex items-center justify-center"
      >
        {/* Deep Background Glows */}
        <div className={`absolute w-[600px] h-[600px] rounded-full blur-[120px] transition-all duration-1000 ${isLooking || isSpeaking ? 'opacity-100' : 'opacity-50'}`} 
             style={{ backgroundColor: activeColor.glow.replace('1)', '0.05)') }} />
        <div className={`absolute w-[300px] h-[300px] rounded-full blur-[80px] transition-all duration-1000 ${isLooking || isSpeaking ? 'opacity-100' : 'opacity-50'}`} 
             style={{ backgroundColor: activeColor.glow.replace('1)', '0.03)') }} />
        
        {isSpeaking && (
          <Motion.div 
            className="absolute w-[400px] h-[400px] rounded-full blur-[60px]"
            style={{ backgroundColor: activeColor.glow.replace('1)', '0.1)') }}
            animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 0.5, repeat: Infinity }}
          />
        )}

        {/* OUTERMOST DECORATIVE RINGS */}
        <Ring size={580} duration={isSpeaking ? 5 : (isLooking ? 40 : 60)} rotateDir={1} opacity={0.03} dashArray="1 20" strokeWidth={0.2} color={`stroke-${activeColor.main}`} />
        <Ring size={540} duration={isSpeaking ? 8 : (isLooking ? 30 : 45)} rotateDir={-1} opacity={0.05} dashArray="20 40" strokeWidth={0.5} color={`stroke-${activeColor.secondary}`} />
        
        {/* TELEMETRY RINGS */}
        <div className="absolute w-[500px] h-[500px] flex items-center justify-center">
          <Ring size={500} duration={isLooking ? 20 : 30} rotateDir={1} opacity={0.1} dashArray="2 8" color={`stroke-${activeColor.main}`} />
          {[0, 90, 180, 270].map(angle => (
            <MicroText 
              key={angle} 
              radius={245} 
              angle={angle} 
              text={isSpeaking ? `VOICE_OUT_${(audioLevel * 100).toFixed(0)}%` : (isLooking ? `LOCKED_${angle}` : `SYNCING_${telemetry}`)} 
            />
          ))}
        </div>

        {/* COMPLEX INTERMEDIATE RINGS */}
        <Ring size={420} duration={isSpeaking ? 12 : (isLooking ? 15 : 25)} rotateDir={-1} opacity={0.15} dashArray="100 20" strokeWidth={1} color={`stroke-${activeColor.main}/40`} />
        <Ring size={380} duration={isSpeaking ? 15 : (isLooking ? 10 : 20)} rotateDir={1} opacity={0.1} dashArray="5 5" strokeWidth={0.3} color={`stroke-${activeColor.secondary}/30`} />
        
        {/* INNER INTERACTIVE RINGS */}
        <Motion.div 
            className="absolute"
            animate={{ scale: isSpeaking ? (1.1 + audioLevel * 0.2) : (isLooking ? [1, 1.1, 1] : [1, 1.02, 1]) }}
            transition={{ duration: isSpeaking ? 0.1 : (isLooking ? 2 : 4), repeat: isSpeaking ? 0 : Infinity, ease: "easeInOut" }}
        >
            <Ring size={320} duration={isSpeaking ? 2 : (isLooking ? 10 : 15)} rotateDir={-1} opacity={0.2} dashArray="40 10" strokeWidth={2} color={`stroke-${activeColor.main}/30`} />
            <Ring size={300} duration={isSpeaking ? 3 : (isLooking ? 5 : 10)} rotateDir={1} opacity={0.3} dashArray="2 4" strokeWidth={0.5} color={`stroke-${activeColor.main}/50`} />
        </Motion.div>

        {/* THE CENTRAL NEURAL CORE */}
        <div className="relative w-48 h-48 flex items-center justify-center">
          <div className={`absolute w-32 h-32 rounded-full blur-[40px] transition-all ${isLooking || isSpeaking ? 'animate-pulse scale-125' : 'animate-pulse'}`} 
               style={{ backgroundColor: activeColor.glow.replace('1)', '0.2)') }} />
          
          <Motion.div 
            className="w-24 h-24 relative flex items-center justify-center"
            animate={{ 
              rotateZ: [0, 360],
              scale: isSpeaking ? (1 + audioLevel * 0.3) : 1
            }}
            transition={{ 
              rotateZ: { duration: isSpeaking ? 2 : (isLooking ? 10 : 20), repeat: Infinity, ease: "linear" },
              scale: { duration: 0.1 }
            }}
          >
            <div className={`absolute inset-0 border rotate-0 rounded-xl blur-[1px] transition-all ${isLooking || isSpeaking ? 'shadow-[0_0_10px_rgba(0,242,255,0.5)]' : ''}`} 
                 style={{ borderColor: activeColor.glow.replace('1)', '0.4)') }} />
            <div className={`absolute inset-0 border rotate-45 rounded-xl blur-[1px] transition-all ${isLooking || isSpeaking ? 'shadow-[0_0_10px_rgba(112,0,255,0.5)]' : ''}`} 
                 style={{ borderColor: activeColor.glow.replace('1)', '0.4)') }} />
            
            <Motion.div 
              className={`w-10 h-10 rounded-sm flex items-center justify-center transition-all border-2 ${isLooking || isSpeaking ? 'scale-110' : ''}`}
              style={{ 
                backgroundColor: activeColor.glow.replace('1)', '0.4)'),
                borderColor: activeColor.glow 
              }}
              animate={{ 
                rotate: [0, 90, 180, 270, 360],
                boxShadow: isSpeaking 
                  ? [`0 0 ${20 + audioLevel * 100}px ${activeColor.glow}`, `0 0 ${40 + audioLevel * 100}px ${activeColor.glow}`]
                  : (isLooking 
                    ? [`0 0 30px ${activeColor.glow}`, `0 0 60px ${activeColor.glow}`, `0 0 30px ${activeColor.glow}`]
                    : [`0 0 20px ${activeColor.glow}`, `0 0 40px ${activeColor.glow}`, `0 0 20px ${activeColor.glow}`])
              }}
              transition={{ duration: isSpeaking ? 0.2 : (isLooking ? 1.5 : 3), repeat: Infinity, ease: "easeInOut" }}
            >
               <div className={`w-2 h-2 bg-white rounded-full ${isLooking || isSpeaking ? 'animate-ping' : 'animate-pulse'}`} />
            </Motion.div>
          </Motion.div>

          <div className="absolute -bottom-16 flex flex-col items-center gap-1">
             <div className="text-[7px] font-mono tracking-[0.4em] uppercase h-4 flex items-center"
                  style={{ color: activeColor.glow.replace('1)', '0.8)') }}>
                <AnimatePresence mode="wait">
                  <Motion.span
                    key={isSpeaking ? "transmitting" : (isLooking ? `active_${emotion}` : scanningText)}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    transition={{ duration: 0.2 }}
                  >
                    {isSpeaking ? "VOICE_ENGINE: TRANSMITTING" : (isLooking ? `USER_ENGAGEMENT: ${emotion.toUpperCase()}` : scanningText)}
                  </Motion.span>
                </AnimatePresence>
             </div>
             <div className="w-24 h-[1px]" style={{ background: `linear-gradient(to right, transparent, ${activeColor.glow}, transparent)` }} />
             <div className="text-[6px] font-mono text-slate-500 uppercase tracking-widest h-3 flex items-center">
                <AnimatePresence mode="wait">
                  <Motion.span
                    key={isSpeaking ? "amp" : (isLooking ? "locked" : stabilityText)}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.1 }}
                  >
                    {isSpeaking ? `AMP: ${(audioLevel * 10).toFixed(2)}` : (isLooking ? "STABILITY: LOCKED" : stabilityText)}
                  </Motion.span>
                </AnimatePresence>
             </div>
          </div>
        </div>

        {/* ORBITING DATA NODES */}
        {Array.from({ length: 12 }).map((_, i) => (
          <Motion.div
            key={i}
            className="absolute pointer-events-none"
            animate={{ rotate: 360 }}
            transition={{ 
              duration: isSpeaking ? (1 + i * 0.2) : (isLooking ? (3 + i * 0.5) : (5 + i)), 
              repeat: Infinity, 
              ease: "linear", 
              delay: i * 0.5 
            }}
          >
            <div 
                className={`w-1 h-1 rounded-full transition-all ${isLooking || isSpeaking ? 'scale-150' : ''}`} 
                style={{ 
                  transform: `translateY(${160 + (i * 10) + (isSpeaking ? audioLevel * 50 : 0)}px)`,
                  backgroundColor: activeColor.glow,
                  boxShadow: `0 0 10px ${activeColor.glow}`
                }}
            />
          </Motion.div>
        ))}

        {/* AXIS MARKERS */}
        <div className="absolute w-[650px] h-[1px] bg-white/[0.03]" />
        <div className="absolute h-[650px] w-[1px] bg-white/[0.03]" />
      </Motion.div>
    </div>
  );
};

export default NeuralSchema;
