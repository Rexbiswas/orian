import { PROXY_BASE_URL, getEnvVar } from '../config';

const VOICE_ID = getEnvVar('VITE_ELEVENLABS_VOICE_ID') || getEnvVar('ELEVENLABS_VOICE_ID') || '21m00Tcm4TlvDq8ikWAM';


// Helper to select the best available English voice in the browser (Desktop & Mobile)
const getEnglishVoice = () => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  return (
    voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Microsoft') || v.name.includes('Samantha') || v.name.includes('Karen') || v.name.includes('Daniel') || v.name.includes('Zira') || v.name.includes('David'))) ||
    voices.find(v => v.lang.startsWith('en') || v.lang === 'en-US' || v.lang === 'en-GB') ||
    voices[0] ||
    null
  );
};

// Explicit mobile audio unlocker to bypass iOS/Android autoplay restrictions
export const unlockAudio = () => {
  if (typeof window === 'undefined') return;
  try {
    // 1. Unlock Web Audio Context
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) {
      const ctx = new AudioCtx();
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const buffer = ctx.createBuffer(1, 1, 22050);
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.start(0);
    }

    // 2. Unlock SpeechSynthesis
    if ('speechSynthesis' in window) {
      window.speechSynthesis.resume();
    }
  } catch (e) {
    // Audio unlock suppressed
  }
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
