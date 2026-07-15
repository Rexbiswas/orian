import React from 'react';

const HUDContainer = ({ children, header, footer }) => {
  return (
    <div className="min-h-screen lg:h-screen w-screen bg-[#020611] text-slate-200 flex flex-col justify-between overflow-y-auto lg:overflow-hidden relative font-mono p-3 select-none">
      
      {/* Cybersecurity scan grid and gradient radial glows */}
      <div className="absolute inset-0 bg-tech-grid pointer-events-none opacity-[0.35]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(138,43,226,0.06),transparent_80%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_15%,rgba(0,229,255,0.04),transparent_65%)] pointer-events-none" />
      
      {/* Optional Top Header */}
      {header && <div className="shrink-0 z-40 mb-3">{header}</div>}

      {/* Main Grid Content */}
      <div className="flex-1 min-h-0 z-30">
        {children}
      </div>

      {/* Optional Bottom Footer */}
      {footer && <div className="shrink-0 z-40 mt-3">{footer}</div>}
      
    </div>
  );
};

export default HUDContainer;
