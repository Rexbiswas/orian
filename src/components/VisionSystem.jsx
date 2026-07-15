import React, { useState, useEffect } from 'react';
import GlassCard from './GlassCard';

const VisionSystem = () => {
  const [elements, setElements] = useState([
    { id: 1, type: 'INPUT', x: 22, y: 38, w: 56, h: 10, label: 'Search Field' },
    { id: 2, type: 'BUTTON', x: 30, y: 62, w: 20, h: 8, label: 'Submit Box' },
    { id: 3, type: 'TEXT', x: 42, y: 15, w: 16, h: 14, label: 'Google Logo' }
  ]);
  const [scanY, setScanY] = useState(0);

  useEffect(() => {
    // Scan animation loop
    const scanInterval = setInterval(() => {
      setScanY(prev => (prev >= 100 ? 0 : prev + 1.5));
    }, 50);

    // Randomize boxes occasionally to look dynamic
    const shuffleInterval = setInterval(() => {
      setElements(prev => prev.map(el => ({
        ...el,
        x: Math.max(10, Math.min(75, el.x + (Math.random() * 8 - 4))),
        y: Math.max(10, Math.min(75, el.y + (Math.random() * 8 - 4)))
      })));
    }, 3000);

    return () => {
      clearInterval(scanInterval);
      clearInterval(shuffleInterval);
    };
  }, []);

  return (
    <GlassCard title="Vision System" className="h-[240px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div className="flex-1 flex flex-col justify-between overflow-hidden min-h-0 pt-1">
        <div className="flex justify-between items-center text-[7px] font-black uppercase text-cyan-400/60 tracking-wider">
          <span>Live Screen Analysis</span>
          <span className="text-emerald-400">YOLOv8: Active</span>
        </div>

        {/* Simulated Screen view */}
        <div className="relative flex-1 bg-[#060813] border border-white/5 rounded my-1.5 overflow-hidden min-h-0">
          {/* Google Mock */}
          <div className="absolute inset-0 flex flex-col items-center justify-center p-3 opacity-30 select-none pointer-events-none scale-90">
            <div className="text-[14px] font-black tracking-tight text-white mb-2 font-sans flex items-center">
              <span className="text-blue-500 font-sans">G</span>
              <span className="text-red-500 font-sans">o</span>
              <span className="text-yellow-500 font-sans">o</span>
              <span className="text-blue-500 font-sans">g</span>
              <span className="text-green-500 font-sans">l</span>
              <span className="text-red-500 font-sans">e</span>
            </div>
            <div className="w-full h-4 border border-white/20 bg-white/5 rounded-full flex items-center px-2 mb-1.5">
              <div className="w-2 h-2 rounded-full border border-white/30 mr-1.5" />
              <div className="w-16 h-1 bg-white/20 rounded" />
            </div>
            <div className="flex gap-1.5">
              <div className="w-12 h-3 border border-white/20 bg-white/5 rounded text-[4px] text-center pt-0.5 text-white/50">Google Search</div>
              <div className="w-12 h-3 border border-white/20 bg-white/5 rounded text-[4px] text-center pt-0.5 text-white/50">I'm Feeling Lucky</div>
            </div>
          </div>

          {/* Dynamic Scan Bounding Boxes */}
          {elements.map(el => (
            <div 
              key={el.id}
              className="absolute border border-emerald-500/80 transition-all duration-700 bg-emerald-500/5"
              style={{
                left: `${el.x}%`,
                top: `${el.y}%`,
                width: `${el.w}%`,
                height: `${el.h}%`
              }}
            >
              {/* Box label info */}
              <span className="absolute -top-3.5 left-0 bg-emerald-500 text-black text-[5px] font-black px-1 py-0.5 rounded-sm uppercase tracking-tighter">
                {el.type}: {el.label}
              </span>
            </div>
          ))}

          {/* Vision Scanner horizontal bar */}
          <div 
            className="absolute left-0 right-0 h-[1.5px] bg-emerald-400/60 shadow-[0_0_5px_rgba(52,211,153,0.7)] animate-scanline"
            style={{ top: `${scanY}%` }}
          />
        </div>

        <div className="flex justify-between items-center text-[6.5px] text-slate-500 font-mono">
          <span>Detected Elements: {elements.length + 11}</span>
          <span className="text-cyan-400/80">SCANNING STATUS: LOCK</span>
        </div>
      </div>
    </GlassCard>
  );
};

export default VisionSystem;
