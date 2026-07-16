import React, { useEffect, useRef, useState } from 'react';
import { useVoice } from '../context/VoiceContext';
import { playMicActivate } from '../utils/sound';
import { WakeLockManager } from './WakeLock';

const WakeWordListener = ({ onWake }) => {
  const { isSpeaking, isListening } = useVoice();
  const [isActive, setIsActive] = useState(false);
  const recognitionRef = useRef(null);
  const wakeLockRef = useRef(new WakeLockManager());
  const shouldListenRef = useRef(true);

  useEffect(() => {
    // Check Web Speech API browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("[WakeWord] Web Speech API is not supported in this browser environment.");
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false; // False is more robust for background restarts on Android Chrome
    rec.interimResults = false;
    rec.lang = 'en-US';

    rec.onstart = () => {
      console.log("[WakeWord] Background microphone listener online.");
      setIsActive(true);
      wakeLockRef.current.request();
    };

    rec.onend = () => {
      setIsActive(false);
      // Auto restart background listener if we aren't active in full command capture or speaking
      if (shouldListenRef.current && !isListening && !isSpeaking) {
        try {
          rec.start();
        } catch (e) {
          // Suppress start overlap warnings
        }
      } else {
        wakeLockRef.current.release();
      }
    };

    rec.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      if (result.isFinal) {
        const transcript = result[0].transcript.trim().toLowerCase();
        console.log(`[WakeWord] Capture: "${transcript}"`);
        
        if (transcript.includes('hello orian') || transcript.includes('orian')) {
          console.log("[WakeWord] MATCH DETECTED!");
          shouldListenRef.current = false;
          rec.stop();
          
          // Play synth chime and invoke wake up sequence
          playMicActivate();
          if (onWake) {
            onWake();
          }
        }
      }
    };

    rec.onerror = (event) => {
      console.log(`[WakeWord] Status: ${event.error}`);
      if (event.error === 'not-allowed') {
        shouldListenRef.current = false; // Stop loop if permission explicitly denied
      }
    };

    recognitionRef.current = rec;

    // Start background listening state
    if (!isListening && !isSpeaking) {
      shouldListenRef.current = true;
      try {
        rec.start();
      } catch (e) {}
    }

    return () => {
      shouldListenRef.current = false;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {}
      }
      wakeLockRef.current.release();
    };
  }, [isSpeaking, isListening, onWake]);

  // Request browser microphone permissions upon first interactive user trigger
  const requestPermission = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      if (recognitionRef.current && !isActive) {
        shouldListenRef.current = true;
        recognitionRef.current.start();
      }
    } catch (err) {
      console.warn("[WakeWord] Microphone permission request rejected:", err);
    }
  };

  return (
    <div className="hidden">
      {/* Invisible button to safely bypass mobile browser user interaction permission guards */}
      <button id="wake-word-permission-trigger" onClick={requestPermission} />
    </div>
  );
};

export default WakeWordListener;
