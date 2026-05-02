import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, Smile, Volume2, Target, Shield, Activity } from 'lucide-react';
import axios from 'axios';

const HumanSenses = ({ onSenseUpdate }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [senses, setSenses] = useState({
    emotion: 'neutral',
    isLooking: false,
    faceCenter: { x: 0.5, y: 0.5 },
    spatial: { azimuth: 0, distance: 1 }
  });
  const [isActive, setIsActive] = useState(true); // Default to true for auto-initialization
  const [stream, setStream] = useState(null);

  useEffect(() => {
    startWebcam();
    return () => stopWebcam();
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
      startAnalysisLoop();
    } catch (err) {
      console.error("Webcam Auto-Access Denied:", err);
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
      if (!videoRef.current) return;

      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const context = canvas.getContext('2d');
      context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      
      canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('frame', blob);

        try {
          const response = await axios.post('http://localhost:5000/api/sense/analyze', formData);
          if (response.data.success) {
            const data = response.data.senses;
            const newSenses = {
              emotion: data.emotion.dominant,
              isLooking: data.engagement.is_looking,
              faceCenter: data.engagement.face_center,
              spatial: data.spatial
            };
            setSenses(newSenses);
            if (onSenseUpdate) onSenseUpdate(newSenses);
          }
        } catch (err) {
          console.error("Sense analysis failed", err);
        }
      }, 'image/jpeg', 0.5);
    }, 2000);

    return () => clearInterval(interval);
  };

  return (
    <div className="fixed bottom-0 right-0 w-1 h-1 opacity-0 pointer-events-none overflow-hidden">
      <video ref={videoRef} autoPlay playsInline muted />
      <canvas ref={canvasRef} width="320" height="240" />
    </div>
  );
};

const SenseMetric = ({ icon: Icon, label, value, color }) => (
  <div className="flex items-center justify-between">
    <div className="flex items-center gap-2">
      <Icon size={12} className="text-slate-500" />
      <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
    </div>
    <span className={`text-[10px] font-black uppercase tracking-widest ${color}`}>{value}</span>
  </div>
);

export default HumanSenses;
