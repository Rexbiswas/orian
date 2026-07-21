import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const VoiceContext = createContext();

export const VoiceProvider = ({ children }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Live User Voice Input (Microphone Listening) Analysis
  const micStreamRef = useRef(null);
  const micAnalyserFrameRef = useRef(null);
  const micAudioContextRef = useRef(null);
  const simIntervalRef = useRef(null);

  const startSimulatedAnalysis = () => {
    stopSimulatedAnalysis();
    let t = 0;
    simIntervalRef.current = setInterval(() => {
      // Simulate syllables and speech envelope fluctuations
      t += 0.18;
      const baseWave = 0.4 + Math.sin(t * 1.6) * 0.35 + Math.sin(t * 0.5) * 0.2;
      const syllableWave = Math.max(0.1, Math.min(1.0, baseWave));
      setAudioLevel(syllableWave);
    }, 45);
  };

  const stopSimulatedAnalysis = () => {
    if (simIntervalRef.current) {
      clearInterval(simIntervalRef.current);
      simIntervalRef.current = null;
    }
  };

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
    stopSimulatedAnalysis();
    setAudioLevel(0);
  };

  const onSpeechEndCallbacks = useRef([]);

  const registerSpeechEndCallback = useCallback((cb) => {
    onSpeechEndCallbacks.current.push(cb);
    return () => {
      onSpeechEndCallbacks.current = onSpeechEndCallbacks.current.filter((c) => c !== cb);
    };
  }, []);

  const setSpeakingState = useCallback((state, audioElement = null) => {
    setIsSpeaking(state);
    if (state) {
      if (audioElement) {
        try {
          startAnalysis(audioElement);
        } catch (e) {
          console.warn("AudioContext blocked or connected. Using simulation fallback.");
          startSimulatedAnalysis();
        }
      } else {
        startSimulatedAnalysis();
      }
    } else {
      stopAnalysis();
      // Notify speech end callbacks to auto reactivate mic
      onSpeechEndCallbacks.current.forEach((cb) => {
        try { cb(); } catch (e) {}
      });
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
