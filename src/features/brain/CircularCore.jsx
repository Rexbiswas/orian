import React, { useRef, useEffect } from 'react';

// Coordinates generator inside ellipsoids representing anatomical lobes for the core brain hologram
const generateLobePoints = (cx, cy, cz, rx, ry, rz, count, type) => {
  const points = [];
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI;
    const phi = Math.random() * Math.PI * 2;
    const shell = 0.85 + 0.15 * Math.random();
    
    let px = cx + rx * Math.sin(theta) * Math.cos(phi) * shell;
    let py = cy + ry * Math.cos(theta) * shell;
    let pz = cz + rz * Math.sin(theta) * Math.sin(phi) * shell;

    const folds = 1.0 + 0.06 * Math.sin(px * 0.35) * Math.cos(py * 0.35);
    px *= folds;
    py *= folds;
    pz *= folds;

    points.push({
      x: px, y: py, z: pz,
      ox: px, oy: py, oz: pz,
      type,
      phase: Math.random() * Math.PI * 2,
      speed: 0.02 + Math.random() * 0.03
    });
  }
  return points;
};

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

const CircularCore = ({ emotion, isSpeaking, isListening, audioLevel }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    let animationId;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    const SIZE = 260;
    canvas.width = SIZE * dpr;
    canvas.height = SIZE * dpr;
    ctx.scale(dpr, dpr);

    const cx = SIZE / 2;
    const cy = SIZE / 2;

    const points = generateBrainPoints();
    
    // Generate floating 3D dust particles around core
    const dustParticles = Array.from({ length: 25 }, () => ({
      x: (Math.random() - 0.5) * 110,
      y: (Math.random() - 0.5) * 90,
      z: (Math.random() - 0.5) * 90,
      vx: (Math.random() - 0.5) * 0.12,
      vy: -0.06 - Math.random() * 0.15,
      vz: (Math.random() - 0.5) * 0.12,
      phase: Math.random() * Math.PI * 2
    }));

    let angleY = Math.PI / 4.5;
    const angleX = 0.22;

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, SIZE, SIZE);
      const isActive = isSpeaking || isListening;
      time += isActive ? 1.8 + audioLevel * 2.0 : 1.0;

      const energyPulse = isActive
        ? 1.0 + audioLevel * 0.35
        : 1.0 + Math.sin(time * 0.04) * 0.04;

      // ── 0. HOLOGRAM SCANLINES BACKGROUND ──────────────────────────────────
      ctx.strokeStyle = 'rgba(138, 46, 255, 0.03)';
      ctx.lineWidth = 0.5;
      for (let y = 15; y < SIZE - 15; y += 2.5) {
        ctx.beginPath();
        ctx.moveTo(15, y);
        ctx.lineTo(SIZE - 15, y);
        ctx.stroke();
      }

      // ── 1. OUTER HUD RINGS (Grid details & Concentric elements) ──────────────────
      // Guide outer circle
      ctx.lineWidth = 0.4;
      ctx.strokeStyle = 'rgba(0, 180, 255, 0.08)';
      ctx.beginPath();
      ctx.arc(cx, cy, 118, 0, Math.PI * 2);
      ctx.stroke();

      // Tick marks
      for (let a = 0; a < 360; a += 4) {
        const rad = (a * Math.PI) / 180;
        const isMajor = a % 20 === 0;
        const isActive = (a + Math.floor(time * 0.25)) % 90 < 20;
        ctx.lineWidth = isMajor ? 1.0 : 0.5;
        ctx.strokeStyle = isActive
          ? `rgba(0, 229, 255, ${isMajor ? 0.65 : 0.4})`
          : `rgba(0, 150, 220, ${isMajor ? 0.2 : 0.08})`;
        const r0 = isMajor ? 110 : 112;
        const r1 = isMajor ? 118 : 115;
        ctx.beginPath();
        ctx.moveTo(cx + r0 * Math.cos(rad), cy + r0 * Math.sin(rad));
        ctx.lineTo(cx + r1 * Math.cos(rad), cy + r1 * Math.sin(rad));
        ctx.stroke();
      }

      // Rotating dashed orbit rings
      ctx.setLineDash([6, 22]);
      ctx.lineWidth = 0.8;
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.35)';
      ctx.beginPath();
      ctx.arc(cx, cy, 104, time * 0.0018, Math.PI * 2 + time * 0.0018);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(30, 80, 255, 0.25)';
      ctx.setLineDash([14, 50]);
      ctx.beginPath();
      ctx.arc(cx, cy, 98, -time * 0.0025, Math.PI * 2 - time * 0.0025);
      ctx.stroke();
      ctx.setLineDash([]);

      // Glowing HUD brackets (cyan and blue)
      ctx.lineWidth = 2.2;
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.7)';
      ctx.shadowColor = '#00e5ff';
      ctx.shadowBlur = 8;
      const ba = time * 0.0008;
      ctx.beginPath(); ctx.arc(cx, cy, 118, ba, ba + 0.18); ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, cy, 118, ba + Math.PI, ba + Math.PI + 0.18); ctx.stroke();
      
      ctx.strokeStyle = 'rgba(30, 100, 255, 0.6)';
      ctx.shadowColor = '#1e64ff';
      const bb = -time * 0.0012;
      ctx.beginPath(); ctx.arc(cx, cy, 118, bb + Math.PI / 2, bb + Math.PI / 2 + 0.18); ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, cy, 118, bb - Math.PI / 2, bb - Math.PI / 2 + 0.18); ctx.stroke();
      ctx.shadowBlur = 0;

      // ── 2. RENDER FLOATING AMBIENT DUST PARTICLES ───────────────────────
      ctx.globalCompositeOperation = 'screen';
      const cosX = Math.cos(angleX);
      const sinX = Math.sin(angleX);
      
      // Update Y rotation based on activity
      angleY += isActive ? 0.005 + audioLevel * 0.015 : 0.0022;
      const cosY = Math.cos(angleY);
      const sinY = Math.sin(angleY);

      // Hologram signal glitch offset
      let glitchOffset = 0;
      if (Math.random() < 0.05) {
        glitchOffset = (Math.random() - 0.5) * 2.0;
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
        // Scaled up brain matching concentric rings bounds
        const px = cx + rx1 * scale * 3.6 * energyPulse + glitchOffset;
        const py = cy - ry1 * scale * 3.6 * energyPulse;

        const opacity = 0.15 + 0.08 * Math.sin(p.phase + time * 0.05);
        ctx.fillStyle = `rgba(168, 85, 247, ${opacity * scale})`;
        ctx.beginPath();
        ctx.arc(px, py, 0.6 * scale, 0, Math.PI * 2);
        ctx.fill();
      });

      // ── 3. PROJECT & RENDER 3D BRAIN NETWORKS ────────────────────────────
      const projected = points.map(pt => {
        let x1 = pt.x * cosY - pt.z * sinY;
        let z1 = pt.x * sinY + pt.z * cosY;
        let y1 = pt.y * cosX - z1 * sinX;
        let z2 = pt.y * sinX + z1 * cosX;

        pt.phase += pt.speed;
        const pulse = 1.0 + 0.02 * Math.sin(pt.phase + time * 0.05);

        const scale = (125 + z2) / 125;
        // Scaled up projection factor from 1.32 to 3.6 to occupy full concentric region
        const px = cx + x1 * scale * pulse * 3.6 * energyPulse + glitchOffset;
        const py = cy - y1 * scale * pulse * 3.6 * energyPulse;

        return {
          px, py, z2,
          ox: pt.ox, oy: pt.oy, oz: pt.oz,
          type: pt.type,
          phase: pt.phase
        };
      });

      // Draw neural filaments (Dual-Pass glow lines)
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

            // Pass 1: Semi-transparent glow backing filament
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.strokeStyle = `rgba(138, 46, 255, ${Math.max(0.01, alpha * 0.45)})`;
            ctx.lineWidth = 1.25;
            ctx.stroke();

            // Pass 2: High bright thin core filament
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.strokeStyle = `rgba(216, 180, 254, ${Math.max(0.02, alpha * 0.95)})`;
            ctx.lineWidth = 0.45;
            ctx.stroke();

            // Animated light sweep pulse running down some connections
            if (i % 3 === 0) {
              const pulseOffset = (time * 0.015 + i * 0.06) % 1.0;
              const pulseX = p1.px + (p2.px - p1.px) * pulseOffset;
              const pulseY = p1.py + (p2.py - p1.py) * pulseOffset;

              ctx.fillStyle = 'rgba(57, 230, 255, 0.95)';
              ctx.shadowColor = '#39e6ff';
              ctx.shadowBlur = 4;
              ctx.beginPath();
              ctx.arc(pulseX, pulseY, 0.85, 0, Math.PI * 2);
              ctx.fill();
              ctx.shadowBlur = 0;
            }
          }
        }
      }

      // Draw thalamus glowing core (center light)
      const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 18 * energyPulse);
      coreGrad.addColorStop(0, '#ffffff');
      coreGrad.addColorStop(0.18, 'rgba(168, 85, 247, 0.85)');
      coreGrad.addColorStop(0.5, 'rgba(138, 43, 226, 0.25)');
      coreGrad.addColorStop(1, 'rgba(57, 230, 255, 0)');
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, 18 * energyPulse, 0, Math.PI * 2);
      ctx.fill();

      // Draw synaptic nodes (particles)
      projected.forEach((p, idx) => {
        const scale = (125 + p.z2) / 125;
        
        if (idx % 7 === 0) {
          ctx.shadowColor = '#d8b4fe';
          ctx.shadowBlur = 4;
          ctx.beginPath();
          ctx.arc(p.px, p.py, 1.35 * scale, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 255, 255, ${0.8 + Math.sin(p.phase) * 0.2})`;
          ctx.fill();
          ctx.shadowBlur = 0;
        } else {
          ctx.beginPath();
          ctx.arc(p.px, p.py, 0.85 * scale, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(168, 85, 247, ${0.4 + Math.sin(p.phase) * 0.15})`;
          ctx.fill();
        }
      });

      // ── 4. HORIZONTAL CYBERNETIC SCANNER sweep line ───────────────────────
      const scanY = cy + Math.sin(time * 0.02) * 55;
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.moveTo(cx - 75, scanY);
      ctx.lineTo(cx + 75, scanY);
      ctx.stroke();

      // ── 5. SCROLLING HUD DATA TEXTS ───────────────────────────────────────
      ctx.font = '500 5px "Roboto Mono", monospace';
      ctx.fillStyle = 'rgba(0, 229, 255, 0.35)';
      const tAngle = time * 0.0014;
      const tRadius = 124;
      ctx.save();
      ctx.translate(cx + tRadius * Math.cos(tAngle), cy + tRadius * Math.sin(tAngle));
      ctx.rotate(tAngle + Math.PI / 2);
      ctx.fillText('ORIAN_COGNITIVE_CORE_V2.0.1 // LIVE_SYNC', -45, 0);
      ctx.restore();

      ctx.globalCompositeOperation = 'source-over';
      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [emotion, isSpeaking, isListening, audioLevel]);

  return (
    <div className="relative w-[260px] h-[260px] flex items-center justify-center select-none">
      {/* Background glow layers */}
      <div className="absolute w-[220px] h-[220px] rounded-full bg-blue-600/5 blur-2xl pointer-events-none animate-pulse" />
      <div className="absolute w-[160px] h-[160px] rounded-full bg-[#8A2EFF]/8 blur-xl pointer-events-none" style={{ animationDelay: '0.5s' }} />
      <canvas
        ref={canvasRef}
        className="z-10"
        style={{ width: '260px', height: '260px' }}
      />
    </div>
  );
};

export default CircularCore;
