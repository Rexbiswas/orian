import React from 'react';
import { motion as Motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

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

const NeuralSchema = ({ isLooking = false }) => {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 25, stiffness: 150 };
  const rotateX = useSpring(useTransform(mouseY, [-300, 300], [15, -15]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-300, 300], [-15, 15]), springConfig);

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
        animate={{ scale: isLooking ? 1.05 : 1 }}
        className="relative flex items-center justify-center"
      >
        {/* Deep Background Glows */}
        <div className={`absolute w-[600px] h-[600px] bg-brand-cyan/5 rounded-full blur-[120px] transition-all duration-1000 ${isLooking ? 'opacity-100' : 'opacity-50'}`} />
        <div className={`absolute w-[300px] h-[300px] bg-brand-purple/5 rounded-full blur-[80px] transition-all duration-1000 ${isLooking ? 'opacity-100' : 'opacity-50'}`} />

        {/* OUTERMOST DECORATIVE RINGS */}
        <Ring size={580} duration={isLooking ? 40 : 60} rotateDir={1} opacity={0.03} dashArray="1 20" strokeWidth={0.2} />
        <Ring size={540} duration={isLooking ? 30 : 45} rotateDir={-1} opacity={0.05} dashArray="20 40" strokeWidth={0.5} />
        
        {/* TELEMETRY RINGS */}
        <div className="absolute w-[500px] h-[500px] flex items-center justify-center">
          <Ring size={500} duration={isLooking ? 20 : 30} rotateDir={1} opacity={0.1} dashArray="2 8" />
          {[0, 90, 180, 270].map(angle => (
            <MicroText key={angle} radius={245} angle={angle} text={isLooking ? `LOCKED_${angle}` : `SEARCHING_${angle}`} />
          ))}
        </div>

        {/* COMPLEX INTERMEDIATE RINGS */}
        <Ring size={420} duration={isLooking ? 15 : 25} rotateDir={-1} opacity={0.15} dashArray="100 20" strokeWidth={1} />
        <Ring size={380} duration={isLooking ? 10 : 20} rotateDir={1} opacity={0.1} dashArray="5 5" strokeWidth={0.3} />
        
        {/* INNER INTERACTIVE RINGS */}
        <Motion.div 
            className="absolute"
            animate={{ scale: isLooking ? [1, 1.1, 1] : [1, 1.02, 1] }}
            transition={{ duration: isLooking ? 2 : 4, repeat: Infinity, ease: "easeInOut" }}
        >
            <Ring size={320} duration={isLooking ? 10 : 15} rotateDir={-1} opacity={0.2} dashArray="40 10" strokeWidth={2} color="stroke-brand-cyan/30" />
            <Ring size={300} duration={isLooking ? 5 : 10} rotateDir={1} opacity={0.3} dashArray="2 4" strokeWidth={0.5} />
        </Motion.div>

        {/* THE CENTRAL NEURAL CORE */}
        <div className="relative w-48 h-48 flex items-center justify-center">
          <div className={`absolute w-32 h-32 bg-brand-cyan/20 rounded-full blur-[40px] transition-all ${isLooking ? 'animate-pulse scale-125' : 'animate-pulse'}`} />
          
          <Motion.div 
            className="w-24 h-24 relative flex items-center justify-center"
            animate={{ rotateZ: [0, 360] }}
            transition={{ duration: isLooking ? 10 : 20, repeat: Infinity, ease: "linear" }}
          >
            <div className={`absolute inset-0 border border-brand-cyan/40 rotate-0 rounded-xl blur-[1px] ${isLooking ? 'border-brand-cyan shadow-[0_0_10px_rgba(0,242,255,0.5)]' : ''}`} />
            <div className={`absolute inset-0 border border-brand-purple/40 rotate-45 rounded-xl blur-[1px] ${isLooking ? 'border-brand-purple shadow-[0_0_10px_rgba(112,0,255,0.5)]' : ''}`} />
            
            <Motion.div 
              className={`w-10 h-10 rounded-sm flex items-center justify-center transition-all ${isLooking ? 'bg-brand-cyan/40 border-brand-cyan border-2 scale-110' : 'bg-brand-cyan/20 border-brand-cyan'}`}
              animate={{ 
                rotate: [0, 90, 180, 270, 360],
                boxShadow: isLooking 
                  ? ["0 0 30px rgba(0,242,255,0.8)", "0 0 60px rgba(0,242,255,1)", "0 0 30px rgba(0,242,255,0.8)"]
                  : ["0 0 20px rgba(0,242,255,0.4)", "0 0 40px rgba(0,242,255,0.8)", "0 0 20px rgba(0,242,255,0.4)"]
              }}
              transition={{ duration: isLooking ? 1.5 : 3, repeat: Infinity, ease: "easeInOut" }}
            >
               <div className={`w-2 h-2 bg-white rounded-full ${isLooking ? 'animate-ping' : 'animate-pulse'}`} />
            </Motion.div>
          </Motion.div>

          <div className="absolute -bottom-16 flex flex-col items-center gap-1">
             <div className="text-[7px] font-mono text-brand-cyan/60 tracking-[0.4em] uppercase">
                {isLooking ? "USER_ENGAGEMENT: ACTIVE" : "SCANNING_FOR_USER"}
             </div>
             <div className="w-24 h-[1px] bg-gradient-to-r from-transparent via-brand-cyan/40 to-transparent" />
             <div className="text-[6px] font-mono text-slate-500 uppercase tracking-widest">
                {isLooking ? "STABILITY: LOCKED" : "STABILITY: FLOATING"}
             </div>
          </div>
        </div>

        {/* ORBITING DATA NODES */}
        {Array.from({ length: 12 }).map((_, i) => (
          <Motion.div
            key={i}
            className="absolute pointer-events-none"
            animate={{ rotate: 360 }}
            transition={{ duration: isLooking ? (3 + i * 0.5) : (5 + i), repeat: Infinity, ease: "linear", delay: i * 0.5 }}
          >
            <div 
                className={`w-1 h-1 bg-brand-cyan rounded-full transition-all ${isLooking ? 'shadow-[0_0_15px_rgba(0,242,255,1)] scale-150' : 'shadow-[0_0_5px_rgba(0,242,255,1)]'}`} 
                style={{ transform: `translateY(${160 + (i * 10)}px)` }}
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
