import React from 'react';
import { motion } from 'framer-motion';

const NeuralPulse = ({ color = "#00f2ff", speed = 1 }) => {
  const points = "0,25 15,25 20,5 25,45 30,25 45,25";
  
  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
      {/* Background Grid Flickers */}
      <div className="absolute inset-0 opacity-20">
        <div className="grid grid-cols-6 grid-rows-4 w-full h-full">
          {Array.from({ length: 24 }).map((_, i) => (
            <motion.div
              key={i}
              animate={{ opacity: [0.1, 0.3, 0.1] }}
              transition={{ 
                duration: Math.random() * 2 + 1, 
                repeat: Infinity, 
                delay: Math.random() * 2 
              }}
              className="border-[0.5px] border-white/5"
            />
          ))}
        </div>
      </div>

      <svg 
        viewBox="0 0 45 50" 
        className="w-full h-3/4 opacity-80 filter drop-shadow-[0_0_8px_rgba(0,242,255,0.5)]"
      >
        <motion.polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ 
            pathLength: [0, 1, 1],
            opacity: [0, 1, 0],
            x: [-10, 0, 10]
          }}
          transition={{
            duration: 1.5 / speed,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        
        {/* Secondary ghost pulse */}
        <motion.polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="0.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.3}
          initial={{ pathLength: 0 }}
          animate={{ 
            pathLength: [0, 1, 0],
            x: [-5, 5, -5]
          }}
          transition={{
            duration: 3 / speed,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      </svg>

    </div>
  );
};

export default NeuralPulse;
