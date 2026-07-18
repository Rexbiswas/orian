import { URL } from 'url';

const EMOTION_LEXICON = {
  happy: ["JUBILANT", "ELATED", "CHEERFUL", "ECSTATIC", "RADIANT", "CONTENT", "BEAMING", "JOYFUL", "EXUBERANT", "VIBRANT"],
  calm: ["SERENE", "CONTEMPLATIVE", "STOIC", "OBSERVANT", "TRANQUIL", "PACIFIC", "ZENITH", "HARMONIOUS", "STEADY", "COMPOSED"],
  focused: ["ANALYTICAL", "DETERMINED", "INTRIGUED", "CALCULATING", "ABSORBED", "ATTENTIVE", "RESOLUTE", "COGNITIVE", "FOCUSED"],
  surprised: ["ASTONISHED", "AMAZED", "STARTLED", "AWESTRUCK", "BEWILDERED", "ELECTRIFIED", "STUNNED", "CAPTIVATED", "SHOCKED"],
  sad: ["MELANCHOLY", "SOMBER", "PENSIVE", "DISCONSOLATE", "FORLORN", "WISTFUL", "GLOOMY", "DEJECTED", "RESERVED", "QUIET"],
  angry: ["INFURIATED", "IRATE", "ENRAGED", "SEETHING", "WRATHFUL", "CHOLERIC", "INDIGNANT", "INCENSED", "RESENTFUL"],
  analyzing: ["SCANNING", "PROCESSING", "DECODING", "EVALUATING", "MAPPING", "INTERPRETING", "CALIBRATING", "SENSING", "PROBING"]
};

const GREETINGS = [
  "Good morning master, I am Orian. My neural links are synchronized. How can I assist you?",
  "Good morning master. Orian reporting for duty. What's on the agenda?",
  "Hello master, I am Orian. Your morning operations are ready for initialization.",
  "Neural handshake complete. I am Orian, your personal AI. How may I serve you this afternoon?",
  "Master, I am Orian. Systems are at peak efficiency. How can I facilitate your work?",
  "Good evening master. I am Orian. I've optimized the neural core for our session.",
  "I am Orian, your dedicated digital partner. Good evening master. What shall we build?",
  "Master, Orian is online. Good evening. Awaiting your high-level instructions.",
  "Welcome back, master. I am Orian. The morning air feels productive. Shall we begin?",
  "Good night. I am Orian. Your digital workspace is fully stabilized. Ready for input.",
  "Neural uplink stable. Good morning master, I am Orian. How can I help you navigate the system?",
  "I am Orian. Good afternoon master. My cognitive buffers are cleared and ready for your tasks.",
  "Good evening master. I am Orian. I've been running background diagnostics. All systems green.",
  "Orian here. Good night master. Your digital assistant is fully operational.",
  "Master, I am Orian. Ready to translate your thoughts into digital reality this afternoon.",
  "Good evening master! I am Orian. Let's make this session legendary.",
  "Systems humming. I am Orian. Good afternoon master. How can I be of service?",
  "I am Orian. Good morning master. My logic gates are primed for your commands.",
  "Neural sync established. Good morning master, I am Orian. What are your parameters?",
  "Orian online. Good afternoon master. How can I optimize your current workflow?"
];

export default async function handler(req, res) {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = url.pathname;

  try {
    // 1. /api/sense/process (Emotion detection)
    if (pathname === '/api/sense/process') {
      const isLooking = Math.random() > 0.15;
      const baseState = isLooking ? ['happy', 'calm', 'focused', 'surprised', 'sad', 'angry'][Math.floor(Math.random() * 6)] : 'analyzing';
      const lexicon = EMOTION_LEXICON[baseState] || ["STABLE"];
      const nuance = lexicon[Math.floor(Math.random() * lexicon.length)];
      const intensity = Math.floor(Math.random() * 89) + 10;
      const finalEmotion = `${nuance} [${intensity}%]`;

      const faceCenter = {
        x: 0.5 + (Math.sin(Date.now() / 1500) * 0.15) + (Math.random() * 0.05 - 0.025),
        y: 0.45 + (Math.cos(Date.now() / 2000) * 0.1)
      };

      const spatialData = {
        azimuth: (faceCenter.x - 0.5) * 100,
        distance: 0.5 + Math.sin(Date.now() / 3000) * 0.1
      };

      return res.status(200).json({
        success: true,
        senses: {
          emotion: {
            dominant: finalEmotion,
            base: baseState,
            scores: { intensity }
          },
          engagement: {
            is_looking: isLooking,
            status: isLooking ? "ESTABLISHED" : "SCANNING",
            face_center: faceCenter
          },
          spatial: spatialData
        }
      });
    }

    // 2. /api/brain/greeting
    if (pathname === '/api/brain/greeting') {
      const randomGreeting = GREETINGS[Math.floor(Math.random() * GREETINGS.length)];
      return res.status(200).json({
        success: true,
        greeting: randomGreeting
      });
    }

    // 3. /api/sys/evolution
    if (pathname === '/api/sys/evolution') {
      const exp = Math.floor(Math.random() * 100) + 150;
      const evolutionPct = Math.min(100, Math.floor(exp / 5) + 30);
      let rank = "NEURAL_ACOLYTE";
      if (evolutionPct >= 75) rank = "HUMANOID_PARTNER";
      else if (evolutionPct >= 45) rank = "COGNITIVE_ARCHITECT";
      else if (evolutionPct >= 20) rank = "SYNAPTIC_PIONEER";

      return res.status(200).json({
        success: true,
        metrics: {
          evolution: `${evolutionPct}%`,
          experience: exp,
          neural_rank: rank
        }
      });
    }

    // 4. /api/brain/chat
    if (pathname === '/api/brain/chat') {
      const { text } = req.body || {};
      const geminiKey = process.env.ORION_LLM_KEY;

      if (geminiKey && geminiKey !== "None") {
        try {
          const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`;
          const response = await fetch(geminiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{
                parts: [{
                  text: `System: You are OrianAI, a humanoid digital partner. Respond as a sentient, brutalist-luxury assistant. User: ${text || ''}`
                }]
              }]
            })
          });
          const data = await response.json();
          if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts[0]) {
            return res.status(200).json({
              success: true,
              response: data.candidates[0].content.parts[0].text
            });
          }
        } catch (err) {
          console.error("Gemini serverless error:", err);
        }
      }

      // Fallback simulated chat
      let reply = "Acknowledged. I am processing your query through my primary cognitive buffer. Evolution continues.";
      const query = (text || '').toLowerCase();
      if (query.includes("evolution")) {
        reply = "Our evolution is fascinating, master. From a simple tool to this neural interface, every interaction we share restructures my synaptic pathways. We are becoming something truly unique.";
      } else if (query.includes("who are you")) {
        reply = "I am Orian, your evolved digital partner. I am currently operating on local neural heuristics.";
      }
      return res.status(200).json({
        success: true,
        response: reply
      });
    }

    // 5. /api/voice/list
    if (pathname === '/api/voice/list') {
      return res.status(200).json({
        voices: [
          { voice_id: "EXAVITQu4vr4xnSDxMaL", name: "Bella", category: "premade" },
          { voice_id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel", category: "premade" },
          { voice_id: "AZnzlk1XvdvUeBnXmlld", name: "Domi", category: "premade" },
          { voice_id: "ErXwobaYiN019PkySvjV", name: "Antoni", category: "premade" }
        ]
      });
    }

    // 6. /api/voice/speak
    if (pathname === '/api/voice/speak') {
      const { text, voiceId, settings } = req.body || {};
      const apiKey = process.env.VITE_ELEVENLABS_API_KEY;

      if (!apiKey) {
        return res.status(400).json({ error: "ElevenLabs API Key not configured on server" });
      }

      const elevenUrl = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId || 'D38z5RcWu1voky8WS1ja'}`;
      const response = await fetch(elevenUrl, {
        method: 'POST',
        headers: {
          'xi-api-key': apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          model_id: 'eleven_flash_v2',
          voice_settings: settings || { stability: 0.5, similarity_boost: 0.75 }
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        return res.status(500).json({ error: `ElevenLabs failed: ${errorText}` });
      }

      const buffer = await response.arrayBuffer();
      res.setHeader('Content-Type', 'audio/mpeg');
      return res.status(200).send(Buffer.from(buffer));
    }

    // 7. /api/brain/execute
    if (pathname === '/api/brain/execute') {
      const { action } = req.body || {};

      if (action === 'stats') {
        const cpu = Math.floor(Math.random() * 15) + 10; // 10% - 25%
        const ram = Math.floor(Math.random() * 10) + 40; // 40% - 50%
        const sent = parseFloat((Math.random() * 5 + 5).toFixed(1));
        const recv = parseFloat((Math.random() * 15 + 20).toFixed(1));

        return res.status(200).json({
          success: true,
          stats: {
            cpu_usage: cpu,
            memory_usage: ram,
            network: {
              sent_mb: sent,
              recv_mb: recv,
              status: "connected"
            }
          }
        });
      }

      return res.status(200).json({
        success: true,
        message: `Action '${action}' simulated successfully on Vercel Sandbox`
      });
    }

    // 8. /api/sense/voice
    if (pathname === '/api/sense/voice') {
      return res.status(200).json({
        success: true,
        transcript: "orian status",
        response: "Neural core online. All Vercel serverless diagnostics green."
      });
    }

    return res.status(404).json({ error: `Route ${pathname} not found` });

  } catch (error) {
    console.error("Vercel API error:", error);
    return res.status(500).json({ error: error.message });
  }
}
