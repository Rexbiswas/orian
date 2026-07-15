import React, { useRef, useEffect } from 'react';

// Recursive midpoint-displacement lightning bolt generator
function drawLightning(ctx, x1, y1, x2, y2, roughness, depth, alpha, color) {
  if (depth <= 0) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = color.replace('ALPHA', alpha);
    ctx.lineWidth = depth === 0 ? 0.6 : 0.4;
    ctx.stroke();
    return;
  }

  const mx = (x1 + x2) / 2 + (Math.random() - 0.5) * roughness;
  const my = (y1 + y2) / 2 + (Math.random() - 0.5) * roughness;

  drawLightning(ctx, x1, y1, mx, my, roughness * 0.55, depth - 1, alpha * 0.9, color);
  drawLightning(ctx, mx, my, x2, y2, roughness * 0.55, depth - 1, alpha * 0.9, color);

  // Random branch
  if (depth > 1 && Math.random() < 0.45) {
    const bx = mx + (Math.random() - 0.5) * roughness * 1.4;
    const by = my + (Math.random() - 0.5) * roughness * 1.4;
    drawLightning(ctx, mx, my, bx, by, roughness * 0.4, depth - 2, alpha * 0.55, color);
  }
}

const CircularCore = ({ emotion, isSpeaking, audioLevel }) => {
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

    let time = 0;
    // Pre-generate stable bolt angles so bolts don't flicker position every frame
    const BOLT_COUNT = 14;
    const boltAngles = Array.from({ length: BOLT_COUNT }, (_, i) =>
      (i * Math.PI * 2) / BOLT_COUNT + (Math.random() * 0.3)
    );
    // Each bolt has an independent activity timer
    const boltActivity = Array.from({ length: BOLT_COUNT }, () => Math.random());

    const render = () => {
      ctx.clearRect(0, 0, SIZE, SIZE);
      time += isSpeaking ? 2.2 + audioLevel * 2.0 : 1.0;

      const energyPulse = isSpeaking
        ? 1.0 + audioLevel * 0.5
        : 1.0 + Math.sin(time * 0.04) * 0.06;

      // ── 1. OUTER HUD RING SYSTEM ──────────────────────────────────────────
      // Guide circle
      ctx.lineWidth = 0.4;
      ctx.strokeStyle = 'rgba(0, 180, 255, 0.09)';
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
          ? `rgba(0, 229, 255, ${isMajor ? 0.6 : 0.35})`
          : `rgba(0, 150, 220, ${isMajor ? 0.22 : 0.1})`;
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
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';
      ctx.beginPath();
      ctx.arc(cx, cy, 104, time * 0.0018, Math.PI * 2 + time * 0.0018);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(30, 80, 255, 0.3)';
      ctx.setLineDash([14, 50]);
      ctx.beginPath();
      ctx.arc(cx, cy, 98, -time * 0.0025, Math.PI * 2 - time * 0.0025);
      ctx.stroke();
      ctx.setLineDash([]);

      // Glowing HUD bracket arcs (cyan)
      ctx.lineWidth = 2.2;
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.7)';
      ctx.shadowColor = '#00e5ff';
      ctx.shadowBlur = 8;
      const ba = time * 0.0008;
      ctx.beginPath(); ctx.arc(cx, cy, 118, ba, ba + 0.18); ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, cy, 118, ba + Math.PI, ba + Math.PI + 0.18); ctx.stroke();
      // Blue brackets
      ctx.strokeStyle = 'rgba(30, 100, 255, 0.65)';
      ctx.shadowColor = '#1e64ff';
      const bb = -time * 0.0012;
      ctx.beginPath(); ctx.arc(cx, cy, 118, bb + Math.PI / 2, bb + Math.PI / 2 + 0.18); ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, cy, 118, bb - Math.PI / 2, bb - Math.PI / 2 + 0.18); ctx.stroke();
      ctx.shadowBlur = 0;

      // ── 2. ELECTRIC PLASMA AURA RINGS ────────────────────────────────────
      // Animate 3 wobbling plasma rings around the ball
      for (let ring = 0; ring < 3; ring++) {
        const ringR = (46 + ring * 12) * energyPulse;
        const segments = 80;
        ctx.beginPath();
        for (let s = 0; s <= segments; s++) {
          const theta = (s * Math.PI * 2) / segments;
          const wobble =
            2.5 * Math.sin(6 * theta + time * 0.04 + ring * 1.2) +
            1.5 * Math.cos(9 * theta - time * 0.03) +
            (ring === 1 ? Math.sin(time * 0.06) * 2 : 0);
          const r = ringR + wobble;
          const x = cx + r * Math.cos(theta);
          const y = cy + r * Math.sin(theta);
          s === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        const alphaVal = [0.55, 0.38, 0.22][ring];
        ctx.strokeStyle = `rgba(0, 200, 255, ${alphaVal})`;
        ctx.lineWidth = [1.2, 0.8, 0.5][ring];
        ctx.shadowColor = '#00c8ff';
        ctx.shadowBlur = [10, 6, 3][ring];
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // ── 3. SWIRLING WAVY PLASMA SPHERE ────────────────────────────────────
      ctx.globalCompositeOperation = 'screen';
      
      const waveLayers = 6;
      for (let j = 0; j < waveLayers; j++) {
        // Spiral rotation over time
        const rotationAngle = (time * 0.006) + (j * Math.PI / waveLayers) * 1.5;
        // Radius fluctuates dynamically
        const baseRadius = (35 + Math.sin(time * 0.02 + j * 0.7) * 8) * energyPulse;
        
        ctx.beginPath();
        ctx.lineWidth = 1.0;
        
        // Multi-color tech gradient (Cyan -> Purple -> Blue)
        const waveGrad = ctx.createLinearGradient(
          cx - baseRadius, cy - baseRadius, 
          cx + baseRadius, cy + baseRadius
        );
        waveGrad.addColorStop(0, 'rgba(0, 229, 255, 0.75)');
        waveGrad.addColorStop(0.4, 'rgba(168, 85, 247, 0.75)');
        waveGrad.addColorStop(0.8, 'rgba(59, 130, 246, 0.75)');
        waveGrad.addColorStop(1, 'rgba(112, 0, 255, 0.75)');
        
        ctx.strokeStyle = waveGrad;
        ctx.shadowColor = j % 2 === 0 ? '#00e5ff' : '#a855f7';
        ctx.shadowBlur = 12;
        
        for (let theta = 0; theta <= Math.PI * 2 + 0.15; theta += 0.04) {
          // Complex frequency modulation to match the target wave orb screenshot
          const freqCount = 4 + (j % 2) * 2;
          const wobble = Math.sin(theta * freqCount + time * 0.1 + j) * 8 * Math.cos(time * 0.015 + j);
          const r = baseRadius + wobble;
          
          const x = cx + r * Math.cos(theta + rotationAngle);
          const y = cy + r * Math.sin(theta + rotationAngle);
          
          if (theta === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
      ctx.globalCompositeOperation = 'source-over';

      // ── 4. GLOWING CENTRAL ORB ────────────────────────────────────────────
      ctx.globalCompositeOperation = 'screen';
      const orbRadius = 14 * energyPulse;
      
      // Radial glow gradient matching screenshot's bright center
      const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, orbRadius * 3.5);
      coreGrad.addColorStop(0, '#ffffff');
      coreGrad.addColorStop(0.15, 'rgba(255, 255, 255, 1)');
      coreGrad.addColorStop(0.3, 'rgba(0, 229, 255, 0.95)');
      coreGrad.addColorStop(0.6, 'rgba(138, 43, 226, 0.5)');
      coreGrad.addColorStop(0.9, 'rgba(59, 130, 246, 0.15)');
      coreGrad.addColorStop(1, 'transparent');
      
      ctx.shadowColor = '#00e5ff';
      ctx.shadowBlur = 24;
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, orbRadius * 3.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.globalCompositeOperation = 'source-over';

      // ── 5. FLOATING ELECTRIC PARTICLES ───────────────────────────────────
      ctx.globalCompositeOperation = 'screen';
      for (let p = 0; p < 30; p++) {
        const pAngle = (p * 13.7 + time * 0.012) % (Math.PI * 2);
        const pDist = 28 + ((p * 7.3 + time * 0.035) % 70);
        const brightness = 0.15 + Math.abs(Math.sin(time * 0.02 + p * 0.8)) * 0.55;
        const pSize = 0.5 + Math.sin(time * 0.04 + p) * 0.35;
        // Alternate between cyan and blue
        const isBlue = p % 3 === 0;
        ctx.fillStyle = isBlue
          ? `rgba(40, 100, 255, ${brightness * 0.7})`
          : `rgba(0, 220, 255, ${brightness})`;
        ctx.shadowColor = isBlue ? '#2864ff' : '#00dcff';
        ctx.shadowBlur = 4;
        ctx.beginPath();
        ctx.arc(
          cx + pDist * Math.cos(pAngle),
          cy + pDist * Math.sin(pAngle),
          pSize, 0, Math.PI * 2
        );
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      ctx.globalCompositeOperation = 'source-over';

      // ── 6. SCROLLING TELEMETRY TEXT ───────────────────────────────────────
      ctx.font = '500 5px "Roboto Mono", monospace';
      ctx.fillStyle = 'rgba(0, 200, 255, 0.35)';
      const tAngle = time * 0.0014;
      const tRadius = 124;
      ctx.save();
      ctx.translate(cx + tRadius * Math.cos(tAngle), cy + tRadius * Math.sin(tAngle));
      ctx.rotate(tAngle + Math.PI / 2);
      ctx.fillText('PLASMA_CORE_V4.1 // LIGHTNING_ACTIVE', -40, 0);
      ctx.restore();

      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [emotion, isSpeaking, audioLevel]);

  return (
    <div className="relative w-[260px] h-[260px] flex items-center justify-center select-none">
      {/* Background glow layers */}
      <div className="absolute w-[220px] h-[220px] rounded-full bg-blue-600/5 blur-2xl pointer-events-none animate-pulse" />
      <div className="absolute w-[160px] h-[160px] rounded-full bg-cyan-400/8 blur-xl pointer-events-none" style={{ animationDelay: '0.5s' }} />
      <canvas
        ref={canvasRef}
        className="z-10"
        style={{ width: '260px', height: '260px' }}
      />
    </div>
  );
};

export default CircularCore;
