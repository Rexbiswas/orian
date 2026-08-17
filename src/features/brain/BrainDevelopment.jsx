import React, { useRef, useEffect, useState } from 'react';

// Scoped custom CSS styles for animations and font loading
const CustomStyles = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;800&family=Space+Grotesk:wght@400;600;700&display=swap');

    @keyframes brain-breath {
      0%, 100% { 
        transform: scale(0.96); 
        filter: drop-shadow(0 0 15px rgba(0, 102, 255, 0.35)); 
      }
      50% { 
        transform: scale(1.04); 
        filter: drop-shadow(0 0 35px rgba(0, 150, 255, 0.65)) drop-shadow(0 0 15px rgba(0, 255, 136, 0.3)); 
      }
    }

    @keyframes light-sweep {
      0% { transform: translateX(-150%) skewX(-20deg); }
      40% { transform: translateX(250%) skewX(-20deg); }
      100% { transform: translateX(250%) skewX(-20deg); }
    }

    @keyframes dot-pulse {
      0%, 100% { 
        transform: scale(1); 
        opacity: 1; 
        box-shadow: 0 0 6px #00FF88, 0 0 12px rgba(0, 255, 136, 0.4); 
      }
      50% { 
        transform: scale(1.4); 
        opacity: 0.7; 
        box-shadow: 0 0 16px #00FF88, 0 0 25px rgba(0, 255, 136, 0.8); 
      }
    }

    .premium-hud-card {
      background: rgba(2, 5, 18, 0.82);
      backdrop-filter: blur(25px);
      box-shadow: 0 0 35px rgba(0, 102, 255, 0.14), 
                  0 0 60px rgba(0, 255, 136, 0.04), 
                  inset 0 0 20px rgba(0, 102, 255, 0.05);
    }

    .premium-hud-subcard {
      background: rgba(1, 4, 16, 0.80);
      border: 1px solid rgba(0, 102, 255, 0.18);
      box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.85);
      background-image: 
        linear-gradient(rgba(0, 102, 255, 0.03) 1px, transparent 1px), 
        linear-gradient(90deg, rgba(0, 102, 255, 0.03) 1px, transparent 1px);
      background-size: 14px 14px;
    }

    .font-orbitron {
      font-family: 'Orbitron', 'Space Grotesk', sans-serif;
    }

    .font-exo {
      font-family: 'Exo 2', 'Space Grotesk', sans-serif;
    }
  `}</style>
);

// Coordinates generator inside ellipsoids representing anatomical lobes
const generateLobePoints = (cx, cy, cz, rx, ry, rz, count, type) => {
  const points = [];
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI;
    const phi = Math.random() * Math.PI * 2;
    const shell = 0.85 + 0.15 * Math.random();
    
    let px = cx + rx * Math.sin(theta) * Math.cos(phi) * shell;
    let py = cy + ry * Math.cos(theta) * shell;
    let pz = cz + rz * Math.sin(theta) * Math.sin(phi) * shell;

    // Folds folds (sulci / gyri)
    const folds = 1.0 + 0.07 * Math.sin(px * 0.35) * Math.cos(py * 0.35);
    px *= folds;
    py *= folds;
    pz *= folds;

    points.push({
      x: px, y: py, z: pz,
      ox: px, oy: py, oz: pz,
      type,
      phase: Math.random() * Math.PI * 2,
      speed: 0.015 + Math.random() * 0.025
    });
  }
  return points;
};

// Generates the points of the cerebrum lobes, cerebellum and brain stem
const generateBrainPoints = () => {
  let points = [];
  const hemispheres = [-1, 1];

  hemispheres.forEach(h => {
    // Frontal Lobe (front-top)
    points = points.concat(generateLobePoints(9 * h, 7, 15, 11, 11, 13, 24, 'frontal'));
    // Parietal Lobe (top-back)
    points = points.concat(generateLobePoints(9 * h, 14, -2, 11, 10, 11, 20, 'parietal'));
    // Occipital Lobe (back-bottom)
    points = points.concat(generateLobePoints(7 * h, 3, -17, 9, 8, 9, 16, 'occipital'));
    // Temporal Lobe (sides-bottom)
    points = points.concat(generateLobePoints(12 * h, -4, 5, 9, 7, 10, 16, 'temporal'));
    // Cerebellum (rear base)
    points = points.concat(generateLobePoints(8 * h, -13, -13, 8, 5.5, 8, 16, 'cerebellum'));
  });

  // Brain stem (central base cylinder)
  points = points.concat(generateLobePoints(0, -21, -3, 3, 9, 3, 14, 'stem'));

  return points;
};

const canConnect = (t1, t2) => {
  if (t1 === t2) return true;
  const adjacencies = {
    'frontal': ['parietal', 'temporal'],
    'parietal': ['frontal', 'occipital', 'temporal'],
    'occipital': ['parietal', 'temporal', 'cerebellum'],
    'temporal': ['frontal', 'parietal', 'occipital', 'cerebellum'],
    'cerebellum': ['occipital', 'temporal', 'stem'],
    'stem': ['cerebellum']
  };
  return adjacencies[t1]?.includes(t2);
};

const BrainDevelopment = ({ evolution = "68.4%" }) => {
  const cardRef = useRef(null);
  const brainCanvasRef = useRef(null);

  // Number animation states
  const [animatedIntelligence, setAnimatedIntelligence] = useState(0);
  const [animatedLearningSpeed, setAnimatedLearningSpeed] = useState(0);
  const [animatedConnections, setAnimatedConnections] = useState(0);
  const [animatedKb, setAnimatedKb] = useState(0);

  // Dropdown states for right column metrics
  const [selectedMetric, setSelectedMetric] = useState('intelligence');
  const [isOpen, setIsOpen] = useState(false);

  // Stats number counting animation
  useEffect(() => {
    const duration = 1800;
    const startTime = performance.now();

    const targetIntel = parseFloat(evolution) || 68.4;
    const targetSpeed = 1.8;
    const targetConn = 12458;
    const targetKb = 2.7;

    let frameId;

    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = progress * (2 - progress);

      setAnimatedIntelligence(ease * targetIntel);
      setAnimatedLearningSpeed(ease * targetSpeed);
      setAnimatedConnections(Math.floor(ease * targetConn));
      setAnimatedKb(ease * targetKb);

      if (progress < 1) {
        frameId = requestAnimationFrame(animate);
      }
    };

    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [evolution]);

  // Canvas render loop for 3D holographic brain
  useEffect(() => {
    let animationId;
    const canvas = brainCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    const width = 180;
    const height = 140;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const cx = width / 2;
    const cy = height / 2 - 2;

    const points = generateBrainPoints();

    // Floating 3D particles around hologram
    const dustParticles = Array.from({ length: 25 }, () => ({
      x: (Math.random() - 0.5) * 115,
      y: (Math.random() - 0.5) * 90,
      z: (Math.random() - 0.5) * 90,
      vx: (Math.random() - 0.5) * 0.1,
      vy: -0.06 - Math.random() * 0.14,
      vz: (Math.random() - 0.5) * 0.1,
      phase: Math.random() * Math.PI * 2
    }));

    let angleY = Math.PI / 4.5;
    const angleX = 0.22;

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      time += 1.0;

      angleY += 0.0035;

      const cosX = Math.cos(angleX);
      const sinX = Math.sin(angleX);
      const cosY = Math.cos(angleY);
      const sinY = Math.sin(angleY);

      // ── 0. HOLOGRAM SCANLINES BACKGROUND ──────────────────────────────────
      ctx.strokeStyle = 'rgba(0, 102, 255, 0.025)';
      ctx.lineWidth = 0.5;
      for (let y = 10; y < height - 10; y += 2.5) {
        ctx.beginPath();
        ctx.moveTo(10, y);
        ctx.lineTo(width - 10, y);
        ctx.stroke();
      }

      // 1. Render floating background dust particles
      let glitchOffset = 0;
      if (Math.random() < 0.04) {
        glitchOffset = (Math.random() - 0.5) * 1.8;
      }

      dustParticles.forEach(p => {
        p.y += p.vy;
        p.x += p.vx;
        p.z += p.vz;

        if (p.y < -50) p.y = 50;
        if (p.x < -60 || p.x > 60) p.vx = -p.vx;
        if (p.z < -50 || p.z > 50) p.vz = -p.vz;

        let rx1 = p.x * cosY - p.z * sinY;
        let rz1 = p.x * sinY + p.z * cosY;
        let ry1 = p.y * cosX - rz1 * sinX;
        let rz2 = p.y * sinX + rz1 * cosX;

        const scale = (120 + rz2) / 120;
        // Increased scale projection factor from 1.35 to 2.25 to make brain larger and fill card
        const px = cx + rx1 * scale * 2.25 * scale + glitchOffset;
        const py = cy - ry1 * scale * 2.25 * scale;

        const opacity = 0.15 + 0.08 * Math.sin(p.phase + time * 0.05);
        ctx.fillStyle = `rgba(0, 120, 255, ${opacity * scale})`;
        ctx.beginPath();
        ctx.arc(px, py, 0.6 * scale, 0, Math.PI * 2);
        ctx.fill();
      });

      // 2. Project 3D brain points
      const projected = points.map(pt => {
        let x1 = pt.x * cosY - pt.z * sinY;
        let z1 = pt.x * sinY + pt.z * cosY;
        let y1 = pt.y * cosX - z1 * sinX;
        let z2 = pt.y * sinX + z1 * cosX;

        pt.phase += pt.speed;
        const pulse = 1.0 + 0.02 * Math.sin(pt.phase + time * 0.06);

        const scale = (125 + z2) / 125;
        // Scale projection factor adjusted from 1.32 to 2.25
        const px = cx + x1 * scale * pulse * 2.25 + glitchOffset;
        const py = cy - y1 * scale * pulse * 2.25;

        return {
          px, py, z2,
          ox: pt.ox, oy: pt.oy, oz: pt.oz,
          type: pt.type,
          phase: pt.phase
        };
      });

      // 3. Draw neural filaments (Dual-Pass glow lines)
      for (let i = 0; i < projected.length; i++) {
        const p1 = projected[i];
        
        for (let j = i + 1; j < projected.length; j++) {
          const p2 = projected[j];

          const isSameHemisphere = (p1.ox * p2.ox > 0) || p1.type === 'stem' || p2.type === 'stem';
          if (!isSameHemisphere) continue;

          if (!canConnect(p1.type, p2.type)) continue;

          const distSq = (p1.ox - p2.ox)**2 + (p1.oy - p2.oy)**2 + (p1.oz - p2.oz)**2;
          const maxDistSq = p1.type === 'cerebellum' || p1.type === 'stem' ? 100 : 155;

          if (distSq < maxDistSq) {
            const dist = Math.sqrt(distSq);
            const alpha = (1.0 - dist / 13.0) * 0.22 * (1.0 + p1.z2 / 120.0);

            // Pass 1: Glowing backing filament — electric blue
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.strokeStyle = `rgba(0, 102, 255, ${Math.max(0.01, alpha * 0.5)})`;
            ctx.lineWidth = 1.1;
            ctx.stroke();

            // Pass 2: High bright core filament — sky blue/white
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.strokeStyle = `rgba(160, 210, 255, ${Math.max(0.015, alpha * 0.9)})`;
            ctx.lineWidth = 0.4;
            ctx.stroke();

            // Animated light sweep pulse — neon green
            if (i % 3 === 0) {
              const pulseOffset = (time * 0.016 + i * 0.06) % 1.0;
              const pulseX = p1.px + (p2.px - p1.px) * pulseOffset;
              const pulseY = p1.py + (p2.py - p1.py) * pulseOffset;

              ctx.fillStyle = 'rgba(0, 255, 136, 0.95)';
              ctx.shadowColor = '#00FF88';
              ctx.shadowBlur = 4;
              ctx.beginPath();
              ctx.arc(pulseX, pulseY, 0.85, 0, Math.PI * 2);
              ctx.fill();
              ctx.shadowBlur = 0;
            }
          }
        }
      }

      // 4. Render glowing thalamus core — electric blue
      const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 18);
      coreGrad.addColorStop(0,    'rgba(255, 255, 255, 0.95)');
      coreGrad.addColorStop(0.18, 'rgba(0, 150, 255, 0.80)');
      coreGrad.addColorStop(0.55, 'rgba(0, 80, 200, 0.25)');
      coreGrad.addColorStop(1,    'rgba(0, 60, 180, 0)');
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, 18, 0, Math.PI * 2);
      ctx.fill();

      // 5. Draw synaptic nodes (particles)
      projected.forEach((p, idx) => {
        const scale = (125 + p.z2) / 125;
        
        if (idx % 7 === 0) {
          ctx.shadowColor = '#60A5FA';
          ctx.shadowBlur = 3;
          ctx.beginPath();
          ctx.arc(p.px, p.py, 1.2 * scale, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(220, 240, 255, ${0.75 + Math.sin(p.phase) * 0.2})`;
          ctx.fill();
          ctx.shadowBlur = 0;
        } else {
          ctx.beginPath();
          ctx.arc(p.px, p.py, 0.7 * scale, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(0, 120, 255, ${0.35 + Math.sin(p.phase) * 0.15})`;
          ctx.fill();
        }
      });

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationId);
  }, []);

  return (
    <>
      <CustomStyles />
      <div 
        ref={cardRef} 
        className="relative rounded-[20px] premium-hud-card flex flex-col pt-6 px-4 pb-3 w-full h-[230px] lg:h-auto lg:flex-1 min-h-0 select-none overflow-hidden font-exo"
      >
        {/* Ambient sliding light sweep sheen — electric blue */}
        <div className="absolute inset-0 overflow-hidden rounded-[20px] pointer-events-none z-10">
          <div className="w-[45%] h-full bg-gradient-to-r from-transparent via-[#0066FF]/6 to-transparent skew-x-12"
               style={{ animation: 'light-sweep 7s infinite linear' }} />
        </div>

        {/* Title Header text (positioned perfectly above the top step-down cut) */}
        <div className="absolute top-2 left-6 z-30">
          <span className="text-[10px] font-black text-white tracking-[0.25em] uppercase select-none font-orbitron">
            Brain Development
          </span>
        </div>

        {/* Outer ambient glow gradients — electric blue */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(0,102,255,0.08),transparent_70%)] pointer-events-none" />
        <div className="absolute inset-0 bg-tech-grid opacity-[0.05] pointer-events-none" />

        {/* Contents splits */}
        <div className="flex-1 flex gap-3.5 overflow-hidden items-center relative z-10">
          
          {/* Left Column: Rotating Brain & Auto-Learning Status */}
          <div className="w-[44%] h-full flex flex-col justify-between items-center pb-0.5">
            <div className="flex-1 w-full relative flex items-center justify-center min-h-0" 
                 style={{ animation: 'brain-breath 5.5s infinite ease-in-out' }}>
              <canvas 
                ref={brainCanvasRef} 
                style={{ width: '180px', height: '140px' }} 
                className="object-contain overflow-visible animate-pulse" 
              />
            </div>
            
            <div className="flex items-center gap-2 bg-[#050A18]/65 border border-[#4CFF88]/20 py-0.5 px-3 rounded-full mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4CFF88]"
                    style={{ animation: 'dot-pulse 1.8s infinite ease-in-out' }} />
              <span className="text-[7.5px] text-[#9AA4C8] uppercase tracking-[0.16em] font-semibold font-exo">
                Auto Learning : <span className="text-[#4CFF88] font-bold">ON</span>
              </span>
            </div>
          </div>

          {/* Right Column: Dynamic Dropdown Selector & Selected Progress Bar */}
          <div className="w-[56%] flex flex-col justify-start gap-2 h-full font-mono text-[9px] premium-hud-subcard rounded-[12px] p-2.5 pl-3.5 relative overflow-visible">
            
            {/* Custom Dropdown Trigger */}
            <div className="relative">
              <span className="text-[6.5px] text-[#8AA4C8] uppercase tracking-wider font-bold block mb-1">Select Metric</span>
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full bg-[#010410] border border-[#0066FF]/35 rounded px-2 py-1 text-[8px] font-bold text-white flex justify-between items-center cursor-pointer shadow-[0_0_8px_rgba(0,102,255,0.08)] hover:border-[#0066FF]/70 transition-all font-mono"
              >
                <span className="capitalize">{selectedMetric === 'learningSpeed' ? 'Learning Speed' : selectedMetric === 'connections' ? 'Connections' : selectedMetric === 'knowledgeBase' ? 'Knowledge Base' : 'Intelligence'}</span>
                <span className="text-[7px] text-blue-400">▼</span>
              </button>
              
              {/* Dropdown Options */}
              {isOpen && (
                <div className="absolute left-0 right-0 mt-1 bg-[#030718]/95 border border-[#0066FF]/40 rounded shadow-2xl z-50 overflow-hidden font-mono">
                  {[
                    { id: 'intelligence', label: 'Intelligence' },
                    { id: 'learningSpeed', label: 'Learning Speed' },
                    { id: 'connections', label: 'Connections' },
                    { id: 'knowledgeBase', label: 'Knowledge Base' }
                  ].map(opt => (
                    <button
                      key={opt.id}
                      onClick={() => {
                        setSelectedMetric(opt.id);
                        setIsOpen(false);
                      }}
                      className="w-full text-left px-2 py-1 text-[7.5px] text-slate-300 hover:bg-[#0066FF]/20 hover:text-white transition-all cursor-pointer font-bold uppercase tracking-wider border-b border-white/[0.02] last:border-none"
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Display Selected Metric Stats */}
            <div className="flex flex-col gap-1.5 mt-2">
              {selectedMetric === 'intelligence' && (
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-end">
                    <span className="text-[7.5px] text-[#8AA4C8] uppercase tracking-wider font-semibold">Intelligence</span>
                    <span className="text-[11px] font-black text-[#00BFFF] font-orbitron leading-none">{animatedIntelligence.toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-2 bg-[#010410] border border-[#0066FF]/25 rounded-full overflow-hidden relative shadow-[inset_0_0_8px_rgba(0,0,0,0.8)] mt-0.5">
                    <div 
                      className="h-full rounded-full bg-gradient-to-r from-[#0044CC] via-[#0088FF] to-[#00FF88] shadow-[0_0_10px_rgba(0,150,255,0.7)] transition-all duration-300"
                      style={{ width: `${animatedIntelligence}%` }}
                    />
                  </div>
                </div>
              )}

              {selectedMetric === 'learningSpeed' && (
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-end">
                    <span className="text-[7.5px] text-[#8AA4C8] uppercase tracking-wider font-semibold">Learning Efficiency</span>
                    <span className="text-[10px] font-black text-[#00BFFF] font-orbitron leading-none">{animatedLearningSpeed.toFixed(1)}x</span>
                  </div>
                  <div className="w-full h-2 bg-[#010410] border border-[#0066FF]/25 rounded-full overflow-hidden relative shadow-[inset_0_0_8px_rgba(0,0,0,0.8)] mt-0.5">
                    <div 
                      className="h-full rounded-full bg-gradient-to-r from-[#0044CC] via-[#0088FF] to-[#00FF88] shadow-[0_0_10px_rgba(0,150,255,0.7)] transition-all duration-300"
                      style={{ width: `${(animatedLearningSpeed / 3.0) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {selectedMetric === 'connections' && (
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-end">
                    <span className="text-[7.5px] text-[#8AA4C8] uppercase tracking-wider font-semibold">Active Nodes</span>
                    <span className="text-[10px] font-black text-[#00BFFF] font-orbitron leading-none">{animatedConnections.toLocaleString()}</span>
                  </div>
                  <div className="w-full h-2 bg-[#010410] border border-[#0066FF]/25 rounded-full overflow-hidden relative shadow-[inset_0_0_8px_rgba(0,0,0,0.8)] mt-0.5">
                    <div 
                      className="h-full rounded-full bg-gradient-to-r from-[#0044CC] via-[#0088FF] to-[#00FF88] shadow-[0_0_10px_rgba(0,150,255,0.7)] transition-all duration-300"
                      style={{ width: `${(animatedConnections / 20000) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {selectedMetric === 'knowledgeBase' && (
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-end">
                    <span className="text-[7.5px] text-[#8AA4C8] uppercase tracking-wider font-semibold">DB Capacity</span>
                    <span className="text-[10px] font-black text-[#00BFFF] font-orbitron leading-none">{animatedKb.toFixed(1)} GB</span>
                  </div>
                  <div className="w-full h-2 bg-[#010410] border border-[#0066FF]/25 rounded-full overflow-hidden relative shadow-[inset_0_0_8px_rgba(0,0,0,0.8)] mt-0.5">
                    <div 
                      className="h-full rounded-full bg-gradient-to-r from-[#0044CC] via-[#0088FF] to-[#00FF88] shadow-[0_0_10px_rgba(0,150,255,0.7)] transition-all duration-300"
                      style={{ width: `${(animatedKb / 5.0) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
            
          </div>

        </div>

      </div>
    </>
  );
};

export default BrainDevelopment;
