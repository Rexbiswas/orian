import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const VoiceContext = createContext();

export const VoiceProvider = ({ children }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  const startAnalysis = (audioElement) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const ctx = audioContextRef.current;
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

  return (
    <VoiceContext.Provider value={{ 
      isSpeaking, 
      isListening, 
      audioLevel, 
      setIsListening, 
      setSpeakingState 
    }}>
      {children}
    </VoiceContext.Provider>
  );
};

export const useVoice = () => useContext(VoiceContext);
