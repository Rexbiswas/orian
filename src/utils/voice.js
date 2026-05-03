const ELEVENLABS_API_KEY = import.meta.env.VITE_ELEVENLABS_API_KEY;
const VOICE_ID = import.meta.env.VITE_ELEVENLABS_VOICE_ID || 'D38z5RcWu1voky8WS1ja';

export const speak = async (text, onStateChange) => {
  // 1. Try ElevenLabs (Simple Proxy or Direct)
  try {
    const response = await fetch(`http://localhost:5000/api/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        voiceId: VOICE_ID,
        settings: { stability: 0.5, similarity_boost: 0.75 }
      }),
    });

    if (response.ok) {
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      if (onStateChange) onStateChange(true, audio);
      
      return new Promise((resolve) => {
        audio.onended = () => {
          if (onStateChange) onStateChange(false);
          resolve();
        };
        audio.play().catch(e => {
          console.error("Audio play failed:", e);
          if (onStateChange) onStateChange(false);
          resolve();
        });
      });
    }
  } catch (error) {
    console.error('Voice failed:', error);
  }

  // 2. Fallback to Native Speech Synthesis
  try {
    const utterance = new SpeechSynthesisUtterance(text);
    if (onStateChange) onStateChange(true);
    
    return new Promise((resolve) => {
      utterance.onend = () => {
        if (onStateChange) onStateChange(false);
        resolve();
      };
      window.speechSynthesis.speak(utterance);
    });
  } catch (e) {
    console.error('Native TTS failed:', e);
    if (onStateChange) onStateChange(false);
  }
};
