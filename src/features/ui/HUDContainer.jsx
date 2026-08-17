import React from 'react';

const HUDContainer = ({ children, header, footer }) => {
  return (
    <div className="min-h-screen lg:h-screen w-full max-w-full bg-[#010208] text-slate-200 flex flex-col justify-between overflow-y-auto lg:overflow-y-hidden relative font-mono p-2.5 select-none">
      
      {/* Advanced tech grid and ambient glow layers */}
      <div className="absolute inset-0 bg-tech-grid pointer-events-none opacity-[0.4]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_60%,rgba(0,102,255,0.07),transparent_75%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_10%_10%,rgba(0,255,136,0.04),transparent_60%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_90%_90%,rgba(0,80,255,0.04),transparent_60%)] pointer-events-none" />
      
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
