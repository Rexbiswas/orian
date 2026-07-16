import React, { useState, useEffect, useRef, useCallback } from 'react';
import GlassCard from './GlassCard';
import { Monitor, Wifi, WifiOff } from 'lucide-react';

const VisionSystem = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const animRef = useRef(null);

  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState(null);
  const [scanY, setScanY] = useState(0);
  const [detectedCount, setDetectedCount] = useState(14);
  const [elements, setElements] = useState([
    { id: 1, type: 'BTN',   x: 22, y: 38, w: 34, h: 12, label: 'UI Button'     },
    { id: 2, type: 'INPUT', x: 10, y: 60, w: 52, h: 10, label: 'Input Field'   },
    { id: 3, type: 'TXT',   x: 42, y: 15, w: 46, h: 10, label: 'Heading Text'  },
  ]);

  /* ── Scan line animation ─────────────────────────────────────── */
  useEffect(() => {
    const t = setInterval(() => {
      setScanY(p => (p >= 100 ? 0 : p + 1.2));
    }, 40);
    /* Jitter bounding boxes */
    const j = setInterval(() => {
      setElements(prev => prev.map(el => ({
        ...el,
        x: Math.max(5, Math.min(70, el.x + (Math.random() * 6 - 3))),
        y: Math.max(5, Math.min(75, el.y + (Math.random() * 6 - 3))),
      })));
      setDetectedCount(c => Math.max(10, Math.min(26, c + Math.floor(Math.random() * 3 - 1))));
    }, 2500);
    return () => { clearInterval(t); clearInterval(j); };
  }, []);

  /* ── Draw live frame to canvas overlay ──────────────────────── */
  const drawFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width  = video.videoWidth  || 320;
    canvas.height = video.videoHeight || 180;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    animRef.current = requestAnimationFrame(drawFrame);
  }, []);

  /* ── Start screen capture ────────────────────────────────────── */
  const startCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 15, width: 640, height: 360 },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setIsCapturing(true);
          drawFrame();
        };
      }
      /* Auto-stop when user ends sharing */
      stream.getVideoTracks()[0].onended = stopCapture;
    } catch (e) {
      setError('Screen share denied or unavailable');
    }
  };

  /* ── Stop screen capture ─────────────────────────────────────── */
  const stopCapture = () => {
    cancelAnimationFrame(animRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsCapturing(false);
  };

  useEffect(() => () => stopCapture(), []);

  /* ── Box label colours ───────────────────────────────────────── */
  const boxColor = (type) => {
    if (type === 'BTN')   return { border: '#00e5ff', bg: 'rgba(0,229,255,0.06)',   label: 'bg-cyan-500'   };
    if (type === 'INPUT') return { border: '#a855f7', bg: 'rgba(168,85,247,0.06)',  label: 'bg-purple-500' };
    return                       { border: '#22c55e', bg: 'rgba(34,197,94,0.06)',   label: 'bg-emerald-500' };
  };

  return (
    <GlassCard title="Vision System" className="h-[240px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
      <div className="flex-1 flex flex-col gap-1.5 overflow-hidden min-h-0">

        {/* Status row */}
        <div className="flex justify-between items-center text-[7px] font-black uppercase tracking-wider shrink-0">
          <span className="text-slate-400">Live Screen Analysis</span>
          <div className="flex items-center gap-1.5">
            <span className={`w-1 h-1 rounded-full ${isCapturing ? 'bg-emerald-400 shadow-[0_0_5px_#22c55e] animate-pulse' : 'bg-slate-600'}`} />
            <span className={isCapturing ? 'text-emerald-400' : 'text-slate-500'}>
              {isCapturing ? 'YOLOv8: ACTIVE' : 'YOLOv8: STANDBY'}
            </span>
          </div>
        </div>

        {/* Screen preview area */}
        <div
          className="relative flex-1 rounded overflow-hidden min-h-0"
          style={{
            background: '#060813',
            border: isCapturing ? '1px solid rgba(0,229,255,0.25)' : '1px solid rgba(255,255,255,0.06)',
            boxShadow: isCapturing ? 'inset 0 0 20px rgba(0,229,255,0.06)' : 'none',
            minHeight: '80px',
          }}
        >
          {/* Hidden video element for screen stream */}
          <video ref={videoRef} className="hidden" muted playsInline />

          {/* Live canvas */}
          {isCapturing && (
            <canvas
              ref={canvasRef}
              className="absolute inset-0 w-full h-full object-contain"
            />
          )}

          {/* Simulated desktop mock when not capturing */}
          {!isCapturing && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-3 opacity-25 select-none pointer-events-none">
              <div className="text-[13px] font-black text-white mb-2 flex gap-0.5">
                <span className="text-blue-400">G</span>
                <span className="text-red-400">o</span>
                <span className="text-yellow-400">o</span>
                <span className="text-blue-400">g</span>
                <span className="text-green-400">l</span>
                <span className="text-red-400">e</span>
              </div>
              <div className="w-full h-3.5 border border-white/20 bg-white/5 rounded-full flex items-center px-2 mb-1.5">
                <div className="w-1.5 h-1.5 rounded-full border border-white/30 mr-1.5" />
                <div className="w-16 h-[3px] bg-white/20 rounded" />
              </div>
              <div className="flex gap-1.5">
                <div className="w-11 h-3 border border-white/20 bg-white/5 rounded text-[4px] text-center pt-0.5 text-white/50">Google Search</div>
                <div className="w-11 h-3 border border-white/20 bg-white/5 rounded text-[4px] text-center pt-0.5 text-white/50">I'm Feeling Lucky</div>
              </div>
            </div>
          )}

          {/* Bounding box overlays */}
          {elements.map(el => {
            const c = boxColor(el.type);
            return (
              <div
                key={el.id}
                className="absolute transition-all duration-700"
                style={{ left: `${el.x}%`, top: `${el.y}%`, width: `${el.w}%`, height: `${el.h}%`, border: `1px solid ${c.border}`, background: c.bg }}
              >
                <span className={`absolute -top-3.5 left-0 ${c.label} text-black text-[4.5px] font-black px-1 py-px rounded-sm uppercase tracking-tight`}>
                  {el.type}: {el.label}
                </span>
              </div>
            );
          })}

          {/* Scanline */}
          <div
            className="absolute left-0 right-0 h-[1.5px] pointer-events-none"
            style={{ top: `${scanY}%`, background: 'rgba(0,229,255,0.5)', boxShadow: '0 0 6px rgba(0,229,255,0.7)' }}
          />

          {/* Start capture overlay button */}
          {!isCapturing && (
            <button
              onClick={startCapture}
              className="absolute inset-0 flex flex-col items-center justify-end pb-2 gap-1 group cursor-pointer"
            >
              <div className="flex items-center gap-1.5 bg-black/60 border border-cyan-400/30 px-2 py-1 rounded-md text-[7px] font-bold text-cyan-400 group-hover:text-cyan-200 group-hover:border-cyan-400/60 group-hover:bg-black/80 transition-all">
                <Monitor size={9} />
                CLICK TO SHARE SCREEN
              </div>
            </button>
          )}
        </div>

        {/* Bottom info row */}
        <div className="flex justify-between items-center text-[6.5px] text-slate-500 font-mono shrink-0">
          <span>Detected Elements: <span className="text-cyan-400/80">{detectedCount}</span></span>
          <button
            onClick={isCapturing ? stopCapture : startCapture}
            className={`flex items-center gap-1 text-[6px] font-black px-1.5 py-0.5 rounded border transition-all cursor-pointer ${
              isCapturing
                ? 'text-red-400 border-red-400/30 hover:bg-red-500/10'
                : 'text-cyan-400 border-cyan-400/30 hover:bg-cyan-400/10'
            }`}
          >
            {isCapturing ? <><WifiOff size={8} /> STOP</> : <><Wifi size={8} /> SCANNING STATUS: LOCK</>}
          </button>
        </div>

        {error && <p className="text-[6px] text-red-400 font-mono truncate">{error}</p>}
      </div>
    </GlassCard>
  );
};

export default VisionSystem;
