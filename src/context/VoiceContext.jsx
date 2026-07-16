import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const VoiceContext = createContext();

export const VoiceProvider = ({ children }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Microphone analysis stream hooks
  const micStreamRef = useRef(null);
  const micAnalyserFrameRef = useRef(null);
  const micAudioContextRef = useRef(null);

  // Live Speech Synthesis (AI Speaking) Analysis
  const startAnalysis = (audioElement) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const ctx = audioContextRef.current;
    if (ctx.state === 'suspended') {
      ctx.resume();
    }
    const source = ctx.createMediaElementSource(audioElement);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyser.connect(ctx.destination);
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const update = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(average / 128); // Normalize to 0-1 approx
      animationFrameRef.current = requestAnimationFrame(update);
    };
    update();
  };

  const stopAnalysis = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    setAudioLevel(0);
  };

  const setSpeakingState = useCallback((state, audioElement = null) => {
    setIsSpeaking(state);
    if (state && audioElement) {
      startAnalysis(audioElement);
    } else {
      stopAnalysis();
    }
  }, []);

  // Live User Voice Input (Microphone Listening) Analysis
  const startMicAnalysis = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      if (!micAudioContextRef.current) {
        micAudioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = micAudioContextRef.current;
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const update = () => {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        // Boost live mic audio responsiveness on the core brain hologram
        setAudioLevel((average / 128) * 1.6);
        micAnalyserFrameRef.current = requestAnimationFrame(update);
      };
      update();
    } catch (err) {
      console.warn("User mic analysis access denied:", err);
    }
  };

  const stopMicAnalysis = () => {
    if (micAnalyserFrameRef.current) {
      cancelAnimationFrame(micAnalyserFrameRef.current);
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(track => track.stop());
      micStreamRef.current = null;
    }
    setAudioLevel(0);
  };

  const setListeningState = useCallback((state) => {
    setIsListening(state);
    if (state) {
      startMicAnalysis();
    } else {
      stopMicAnalysis();
    }
  }, []);

  return (
    <VoiceContext.Provider value={{ 
      isSpeaking, 
      isListening, 
      audioLevel, 
      setIsListening: setListeningState, 
      setSpeakingState 
    }}>
      {children}
    </VoiceContext.Provider>
  );
};

export const useVoice = () => useContext(VoiceContext);
