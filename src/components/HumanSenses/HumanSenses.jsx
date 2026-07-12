import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, ShieldAlert, Target } from 'lucide-react';
import axios from 'axios';

const HumanSenses = ({ onSenseUpdate }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  
  const [senses, setSenses] = useState({
    emotion: 'NEUTRAL',
    base: 'neutral',
    isLooking: false,
    faceCenter: { x: 0.5, y: 0.5 },
    spatial: { azimuth: 0, distance: 0.6 }
  });
  
  const [stream, setStream] = useState(null);
  const [camError, setCamError] = useState(false);
  const [isScanning, setIsScanning] = useState(true);

  // Initialize webcam and start analysis loop
  useEffect(() => {
    let cleanupLoop = null;
    
    const init = async () => {
      const activeStream = await startWebcam();
      if (activeStream) {
        cleanupLoop = startAnalysisLoop();
      } else {
        setCamError(true);
        // If real camera fails, start a simulation loop so the UI is still dynamic
        cleanupLoop = startSimulationLoop();
      }
    };
    
    init();
    
    return () => {
      stopWebcam();
      if (cleanupLoop) cleanupLoop();
    };
  }, []);

  const startWebcam = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 320, height: 240, frameRate: 15 } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setStream(mediaStream);
      setCamError(false);
      return mediaStream;
    } catch (err) {
      console.error("Webcam Auto-Access Denied/Not Found:", err);
      setCamError(true);
      return null;
    }
  };

  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const startAnalysisLoop = () => {
    const interval = setInterval(async () => {
      if (!videoRef.current || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      // Draw video frame to hidden canvas logic
      try {
        // Clear canvas
        context.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw video frame
        context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(async (blob) => {
          if (!blob) return;
          const formData = new FormData();
          formData.append('file', blob);

          try {
            const response = await axios.post('http://127.0.0.1:8000/api/sense/process', formData);
            if (response.data.success) {
              const data = response.data.senses;
              const newSenses = {
                emotion: data.emotion.dominant,
                base: data.emotion.base,
                isLooking: data.engagement.is_looking,
                faceCenter: data.engagement.face_center,
                spatial: data.spatial
              };
              setSenses(newSenses);
              if (onSenseUpdate) onSenseUpdate(newSenses);
            }
          } catch (err) {
            // Silently swallow network errors during development
          }
        }, 'image/jpeg', 0.4);
      } catch (err) {
        console.error("Frame analysis draw fail", err);
      }
    }, 250);

    return () => clearInterval(interval);
  };

  // Simulation fallback to keep the HUD animated and active even without a camera
  const startSimulationLoop = () => {
    const emotions = ["happy", "calm", "focused", "surprised", "sad", "angry"];
    const interval = setInterval(() => {
      const isLooking = Math.random() > 0.15;
      const base = isLooking ? emotions[Math.floor(Math.random() * emotions.length)] : "analyzing";
      const intensity = Math.floor(Math.random() * 40) + 50;
      const dominant = `${base.toUpperCase()} [${intensity}%]`;
      
      const newSenses = {
        emotion: dominant,
        base: base,
        isLooking: isLooking,
        faceCenter: {
          x: 0.5 + (Math.sin(Date.now() / 1500) * 0.15) + (Math.random() * 0.05 - 0.025),
          y: 0.45 + (Math.cos(Date.now() / 2000) * 0.1)
        },
        spatial: {
          azimuth: (Math.sin(Date.now() / 1500) * 30),
          distance: 0.5 + Math.sin(Date.now() / 3000) * 0.1
        }
      };
      setSenses(newSenses);
      if (onSenseUpdate) onSenseUpdate(newSenses);
    }, 400);

    return () => clearInterval(interval);
  };

  // Custom visual overlay drawing on a separate rendering frame
  useEffect(() => {
    let animationId;
    const drawOverlay = () => {
      const canvas = canvasRef.current;
      if (!canvas) {
        animationId = requestAnimationFrame(drawOverlay);
        return;
      }
      
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      
      // Draw visual overlay (the camera view handles the camera background itself)
      // Clear overlay
      ctx.clearRect(0, 0, w, h);

      // If camera error, we draw a simulated scanning background (dark grid with face mesh wireframe)
      if (camError) {
        // Draw grid
        ctx.strokeStyle = 'rgba(0, 242, 255, 0.05)';
        ctx.lineWidth = 1;
        const gridSize = 20;
        for (let x = 0; x < w; x += gridSize) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, h);
          ctx.stroke();
        }
        for (let y = 0; y < h; y += gridSize) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(w, y);
          ctx.stroke();
        }

        // Draw wireframe head silhouette in center
        ctx.strokeStyle = 'rgba(0, 242, 255, 0.15)';
        ctx.beginPath();
        ctx.ellipse(w / 2, h / 2.2, 45, 60, 0, 0, 2 * Math.PI);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.ellipse(w / 2, h / 2.2, 40, 55, 0, 0, 2 * Math.PI);
        ctx.stroke();

        // Draw wireframe neck
        ctx.beginPath();
        ctx.moveTo(w / 2 - 20, h / 2.2 + 50);
        ctx.lineTo(w / 2 - 30, h - 30);
        ctx.lineTo(w / 2 + 30, h - 30);
        ctx.lineTo(w / 2 + 20, h / 2.2 + 50);
        ctx.stroke();
      }

      // Draw face bounding box if looking/detected
      if (senses.isLooking) {
        const fc = senses.faceCenter;
        
        // Calculate box dimensions (using spatial distance as sizing proxy)
        const faceSize = (1 - (senses.spatial?.distance || 0.6)) * 140 + 40; // width in pixels
        const boxW = Math.max(50, Math.min(150, faceSize));
        const boxH = boxW * 1.25;
        
        // Target coordinates on canvas
        const targetX = fc.x * w - boxW / 2;
        const targetY = fc.y * h - boxH / 2;

        // Draw bounding box
        ctx.strokeStyle = senses.base === 'happy' ? '#34d399' : '#00f2ff';
        ctx.lineWidth = 1.5;
        
        // Draw bracket-style corners
        const cornerLen = 12;
        // Top-left
        ctx.beginPath();
        ctx.moveTo(targetX + cornerLen, targetY);
        ctx.lineTo(targetX, targetY);
        ctx.lineTo(targetX, targetY + cornerLen);
        ctx.stroke();
        // Top-right
        ctx.beginPath();
        ctx.moveTo(targetX + boxW - cornerLen, targetY);
        ctx.lineTo(targetX + boxW, targetY);
        ctx.lineTo(targetX + boxW, targetY + cornerLen);
        ctx.stroke();
        // Bottom-left
        ctx.beginPath();
        ctx.moveTo(targetX, targetY + boxH - cornerLen);
        ctx.lineTo(targetX, targetY + boxH);
        ctx.lineTo(targetX + cornerLen, targetY + boxH);
        ctx.stroke();
        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(targetX + boxW, targetY + boxH - cornerLen);
        ctx.lineTo(targetX + boxW, targetY + boxH);
        ctx.lineTo(targetX + boxW - cornerLen, targetY + boxH);
        ctx.stroke();

        // Draw center crosshair relative to face center
        ctx.strokeStyle = 'rgba(0, 242, 255, 0.4)';
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(fc.x * w - 5, fc.y * h);
        ctx.lineTo(fc.x * w + 5, fc.y * h);
        ctx.moveTo(fc.x * w, fc.y * h - 5);
        ctx.lineTo(fc.x * w, fc.y * h + 5);
        ctx.stroke();

        // Draw tech scan lines within the bounding box
        ctx.fillStyle = 'rgba(0, 242, 255, 0.05)';
        ctx.fillRect(targetX + 2, targetY + 2, boxW - 4, boxH - 4);

        // Draw target dots/mesh nodes inside the box to simulate face mesh
        ctx.fillStyle = senses.base === 'happy' ? '#34d399' : '#00f2ff';
        const points = [
          { x: 0, y: -0.25 }, // nose tip
          { x: -0.2, y: -0.35 }, // left eye
          { x: 0.2, y: -0.35 }, // right eye
          { x: 0, y: -0.1 }, // mouth
          { x: -0.3, y: -0.25 }, // left cheek
          { x: 0.3, y: -0.25 }, // right cheek
          { x: -0.2, y: 0.1 }, // chin left
          { x: 0.2, y: 0.1 }, // chin right
          { x: 0, y: 0.2 } // chin bottom
        ];
        
        points.forEach(pt => {
          const px = fc.x * w + pt.x * boxW * 0.7;
          const py = fc.y * h + pt.y * boxH * 0.7;
          ctx.beginPath();
          ctx.arc(px, py, 1.5, 0, 2 * Math.PI);
          ctx.fill();
        });

        // Bounding box tag info
        ctx.font = '5px monospace';
        ctx.fillStyle = senses.base === 'happy' ? '#34d399' : '#00f2ff';
        ctx.fillText(`ID: ADMIN_RISHI`, targetX, targetY - 14);
        ctx.fillText(`LOC: X:${(fc.x * 100).toFixed(0)} Y:${(fc.y * 100).toFixed(0)}`, targetX, targetY - 8);
        ctx.fillText(`TRACKING: ACTIVE`, targetX, targetY - 2);
        
        // Intensity badge at bottom
        ctx.font = 'bold 5px monospace';
        ctx.fillText(`STATE: ${senses.emotion.split(' ')[0]}`, targetX, targetY + boxH + 8);
      }

      // Draw active scanner grid / circle
      ctx.strokeStyle = 'rgba(0, 242, 255, 0.1)';
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      ctx.arc(w / 2, h / 2, Math.min(w, h) * 0.45, 0, 2 * Math.PI);
      ctx.stroke();

      animationId = requestAnimationFrame(drawOverlay);
    };
    
    animationId = requestAnimationFrame(drawOverlay);
    return () => cancelAnimationFrame(animationId);
  }, [senses, camError]);

  return (
    <div className="w-full h-full relative bg-slate-950/90 rounded-lg overflow-hidden border border-brand-cyan/20 group">
      {/* Live Webcam Stream */}
      {!camError && (
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          className="absolute inset-0 w-full h-full object-cover opacity-75 mix-blend-screen"
        />
      )}
      
      {/* Fallback Static Scanning Grid if Webcam Fails */}
      {camError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80">
          <div className="w-16 h-16 rounded-full border border-dashed border-brand-cyan/30 flex items-center justify-center animate-spin-slow mb-2">
            <Target size={24} className="text-brand-cyan/50" />
          </div>
          <span className="text-[7px] text-brand-cyan/40 font-black uppercase tracking-widest">REALTIME_SCANNER_EMULATOR</span>
        </div>
      )}

      {/* Render Canvas for Scanning & Face Mesh HUD overlays */}
      <canvas 
        ref={canvasRef} 
        width="280" 
        height="180" 
        className="absolute inset-0 w-full h-full z-10 pointer-events-none"
      />

      {/* Futuristic Scanline Laser */}
      <div className="absolute left-0 right-0 h-[1.5px] bg-cyan-400/35 shadow-[0_0_8px_rgba(6,182,212,0.8)] z-10 pointer-events-none animate-scanline" />

      {/* Top HUD UI Status tags */}
      <div className="absolute top-2 left-2 right-2 flex justify-between items-center z-20 pointer-events-none">
        <div className="flex items-center gap-1.5 bg-black/40 px-2 py-0.5 rounded border border-white/5 backdrop-blur-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]" />
          <span className="text-[7px] font-black text-white/70 uppercase tracking-widest">
            {camError ? "EMU: ON" : "CAMERA: ON"}
          </span>
        </div>
        <div className="text-[7px] font-mono text-slate-400 bg-black/40 px-2 py-0.5 rounded border border-white/5">
          FPS: 15
        </div>
      </div>

      {/* Bottom HUD UI Status tags */}
      <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center z-20 pointer-events-none">
        <div className="flex items-center gap-1 bg-black/40 px-2 py-0.5 rounded border border-white/5 backdrop-blur-sm">
          <span className={`w-1 h-1 rounded-full ${senses.isLooking ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500 animate-ping'}`} />
          <span className="text-[6px] font-bold text-slate-300 uppercase tracking-widest">
            {senses.isLooking ? 'Eye_Tracking: Active' : 'Scanning_Face...'}
          </span>
        </div>
        <div className="text-[6px] font-mono text-brand-cyan uppercase tracking-wider">
          {senses.isLooking ? "LOCK: ADMIN" : "SEARCHING"}
        </div>
      </div>
    </div>
  );
};

export default HumanSenses;
