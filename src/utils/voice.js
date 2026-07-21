import { PROXY_BASE_URL } from '../config';

const VOICE_ID = import.meta.env.VITE_ELEVENLABS_VOICE_ID || 'D38z5RcWu1voky8WS1ja';

// Helper to select the best available English voice in the browser
const getEnglishVoice = () => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  return (
    voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Microsoft') || v.name.includes('Zira') || v.name.includes('David') || v.name.includes('Samantha'))) ||
    voices.find(v => v.lang.startsWith('en')) ||
    voices[0] ||
    null
  );
};

// Ensure browser voices are preloaded
if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    try { window.speechSynthesis.getVoices(); } catch (e) {}
  };
}

export const speak = async (text, onStateChange) => {
  if (!text) return;

  // 1. Try ElevenLabs (Simple Proxy or Direct)
  try {
    const response = await fetch(`${PROXY_BASE_URL}/api/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        voiceId: VOICE_ID,
        settings: { stability: 0.5, similarity_boost: 0.75 }
      }),
    });

    if (!response.ok) {
      throw new Error(`ElevenLabs speech proxy returned status ${response.status}`);
    }

    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    if (onStateChange) onStateChange(true, audio);
    
    return new Promise((resolve) => {
      let resolved = false;
      const done = () => {
        if (!resolved) {
          resolved = true;
          if (onStateChange) onStateChange(false);
          resolve();
        }
      };
      audio.onended = done;
      audio.onerror = done;
      audio.play().catch(e => {
        console.warn("ElevenLabs audio play failed:", e);
        done();
      });
      setTimeout(done, Math.max(3000, text.length * 150));
    });
  } catch (error) {
    console.warn('ElevenLabs voice generation unavailable, using native browser TTS fallback:', error.message || error);
  }

  // 2. Fallback to Native Speech Synthesis (High Compatibility Browser Speech)
  try {
    if (!('speechSynthesis' in window)) {
      if (onStateChange) onStateChange(false);
      return;
    }
    
    // Resume if synthesis engine was paused by browser policy
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    window.speechSynthesis.cancel(); // Clear queued speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.volume = 1.0; // Max volume
    utterance.rate = 1.0;   // Normal speed
    utterance.pitch = 1.0;  // Normal pitch

    const selectedVoice = getEnglishVoice();
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    if (onStateChange) onStateChange(true);
    
    return new Promise((resolve) => {
      let resolved = false;
      const done = () => {
        if (!resolved) {
          resolved = true;
          if (onStateChange) onStateChange(false);
          resolve();
        }
      };

      utterance.onend = done;
      utterance.onerror = (e) => {
        console.warn("Native SpeechSynthesis error:", e);
        done();
      };

      // Unpause and speak
      window.speechSynthesis.resume();
      window.speechSynthesis.speak(utterance);
      
      // Safety timeout: max 400ms per word or minimum 2.5s
      const words = text.split(' ').length;
      const maxMs = Math.max(2500, words * 400);
      setTimeout(done, maxMs);
    });
  } catch (e) {
    console.error('Native TTS failed:', e);
    if (onStateChange) onStateChange(false);
  }
};
