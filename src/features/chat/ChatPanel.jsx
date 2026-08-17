import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { AudioLines, Terminal, Cpu, Sparkles, X, Command } from 'lucide-react';
import { useLogs } from '../../context/LogContext';
import { useVoice } from '../../context/VoiceContext';
import { speak } from '../../utils/voice';
import { motion } from 'framer-motion';
import axios from 'axios';
import { AudioRecorder } from '../../utils/audioRecorder';
import { API_BASE_URL } from '../../config';

const DownloadProgress = ({ label }) => {
  const [progress, setProgress] = useState(0);
  const isComplete = progress >= 100;

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          return 100;
        }
        return p + Math.random() * 25;
      });
    }, 400);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mt-2 w-full space-y-1">
      <div className="flex justify-between text-[8px] font-black uppercase transition-colors">
        <span className={isComplete ? "text-emerald-400" : "text-brand-cyan/60"}>
          {isComplete ? `SYNC_COMPLETE_${label}` : `Syncing_${label}`}
        </span>
        <span className={isComplete ? "text-emerald-400" : "text-slate-400"}>
          {isComplete ? "SUCCESS" : `${Math.round(progress)}%`}
        </span>
      </div>
      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          className={`h-full transition-colors duration-500 ${isComplete ? "bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.6)]" : "bg-brand-cyan shadow-[0_0_10px_rgba(0,242,255,0.5)]"
            }`}
        />
      </div>
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[7px] text-emerald-400/80 font-bold uppercase tracking-tighter"
        >
          Neural signatures integrated. Evolution metrics updated.
        </motion.div>
      )}
    </div>
  );
};

const ChatPanel = ({ onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const { addLog } = useLogs();
  const { setSpeakingState } = useVoice();
  const scrollRef = useRef(null);
  const recorderRef = useRef(new AudioRecorder());

  // Dynamic Greeting on mount
  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/brain/greeting`);
        const greeting = res.data.greeting;
        setMessages([{ id: 1, role: 'ai', text: greeting }]);
      } catch (err) {
        setMessages([{ id: 1, role: 'ai', text: "Hello Master! i am orian, your personal ai assistant. Neural link established." }]);
      }
    };
    if (messages.length === 0) fetchGreeting();
  }, []);

  const toggleListening = async () => {
    if (isListening) {
      setIsListening(false);
      addLog('VOICE_STREAM_STOPPED', 'MIC', 'INFO');

      try {
        const audioBlob = await recorderRef.current.stop();
        addLog('UPLOADING_NEURAL_AUDIO', 'SYS', 'INFO');

        const formData = new FormData();
        formData.append('file', audioBlob, 'command.wav');

        const res = await axios.post(`${API_BASE_URL}/api/sense/voice`, formData);

        if (res.data.success) {
          const transcript = res.data.text;
          setInput(transcript);
          addLog(`NEURAL_STT_SYNC: "${transcript}"`, 'BRAIN', 'SUCCESS');
          handleSend(transcript);
        } else {
          addLog(`STT_FAULT: ${res.data.message}`, 'BRAIN', 'ERROR');
        }
      } catch (err) {
        addLog('MIC_UPLINK_CRITICAL_FAILURE', 'SYS', 'ERROR');
      }
    } else {
      try {
        await recorderRef.current.start();
        setIsListening(true);
        addLog('NEURAL_MIC_UPLINK_ESTABLISHED', 'MIC', 'SUCCESS');
      } catch (err) {
        addLog('MIC_ACCESS_DENIED', 'SYS', 'ERROR');
      }
    }
  };

  const handleSend = async (overrideInput = null) => {
    const textToSend = overrideInput || input;
    if (!textToSend.trim()) return;

    const userMsg = { id: Date.now(), role: 'user', text: textToSend };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    addLog(`INIT_QUERY: "${textToSend}"`, 'EXEC', 'INFO');

    try {
      // 1. Detect if it's a command for the Brain
      const commandLower = textToSend.toLowerCase();
      let responseText = '';

      if (commandLower === 'clear') {
        addLog('CHAT_TERMINATED_BY_USER', 'SYS', 'INFO');
        setMessages([
          { id: Date.now(), role: 'ai', text: 'Neural buffer cleared. System ready for new queries.' }
        ]);
        setInput('');
        setIsTyping(false);
        return;
      }

      if (commandLower.includes('open') || commandLower.includes('launch')) {
        const app = commandLower.replace('open ', '').replace('launch ', '').trim();
        addLog(`COMMAND_DETECTED: LAUNCH_${app.toUpperCase()}`, 'BRAIN', 'INFO');

        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, {
          action: 'launch',
          payload: app
        });

        if (res.data.success) {
          responseText = `Protocol executed. ${app} is now online.`;
          addLog(`CMD_SUCCESS: ${app}`, 'SYS', 'SUCCESS');
        } else {
          responseText = `Failed to initialize ${app}. Searching for neural corrections...`;
          addLog(`CMD_FAILURE: ${app}`, 'SYS', 'ERROR');
        }
      } else if (commandLower.match(/(volume|sound|audio|mute)/i)) {
        const vol = commandLower.match(/\d+/)?.[0] || "50";
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'setting', payload: 'volume', key: vol });
        responseText = res.data.success ? res.data.message : `System Warning: ${res.data.message || res.data.error || 'Operation failed'}`;
      } else if (commandLower.match(/(bright|brit|brith|light)/i) && commandLower.includes('to')) {
        const level = commandLower.match(/\d+/)?.[0] || "100";
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'setting', payload: 'brightness', key: level });
        responseText = res.data.success ? res.data.message : `Optical Warning: ${res.data.message || res.data.error || 'Display unavailable'}`;
      } else if (commandLower.match(/(dark mode|light mode|theme)/i)) {
        const mode = commandLower.includes('dark') ? 'dark mode' : 'light mode';
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'setting', payload: mode });
        responseText = res.data.success ? res.data.message : `UI Warning: ${res.data.message || res.data.error || 'Theme change failed'}`;
      } else if (commandLower.match(/(wifi|wi-fi|internet|network)/i) && (commandLower.includes('on') || commandLower.includes('off'))) {
        const state = commandLower.includes('on') ? 'on' : 'off';
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'setting', payload: 'wifi', key: state });
        responseText = res.data.success ? res.data.message : `Uplink Warning: ${res.data.message || res.data.error || 'Network error'}`;
      } else if (commandLower.includes('meeting')) {
        const action = commandLower.includes('summarize') ? 'summarize' : 'start';
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'meeting', payload: action });
        responseText = res.data.message;
      } else if (commandLower.includes('translate')) {
        const parts = commandLower.split(' to ');
        const textToTranslate = parts[0].replace('translate ', '');
        const targetLang = parts[1] || 'spanish';
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'translate', payload: textToTranslate, key: targetLang });
        responseText = res.data.translation;
      } else if (commandLower.includes('screenshot')) {
        await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'screenshot' });
        responseText = "Neural snapshot captured and stored in central database.";
      } else if (commandLower.includes('stats') || commandLower.includes('status')) {
        const res = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'stats' });
        const s = res.data.stats;
        responseText = `System Integrity: CPU ${s.cpu_usage}%, RAM ${s.memory_usage}%. Neural nodes active: ${s.active_apps}.`;
      } else {
        // Dynamic Neural Processing (Fallback to Python Brain)
        const isDownload = commandLower.includes('download') || commandLower.includes('skill');

        if (isDownload) {
          const skillName = commandLower.replace('download', '').replace('skill', '').trim().toUpperCase() || 'NEURAL';
          const downloadMsgId = Date.now();

          setMessages(prev => [...prev, {
            id: downloadMsgId,
            role: 'ai',
            text: `Initializing high-speed uplink for ${skillName} package...`,
            type: 'download',
            skillLabel: skillName
          }]);

          // Execute actual backend integration in parallel
          axios.post(`${API_BASE_URL}/api/brain/chat`, { text: textToSend }).then(res => {
            setTimeout(() => {
              setMessages(prev => prev.map(m =>
                m.id === downloadMsgId ? { ...m, text: res.data.response, type: 'text' } : m
              ));
            }, 3000);
          }).catch(err => {
            setMessages(prev => prev.map(m =>
              m.id === downloadMsgId ? { ...m, text: "Uplink Failure. Neural core unreachable.", type: 'text' } : m
            ));
          });

          setInput('');
          setIsTyping(false);
          return;
        }

        // --- ORION_NEURAL_GATEKEEPER (Bulletproof Persona) ---
        const metaWords = ["who are you", "what are you", "tell me your self", "identity", "persona", "framing", "anthropic", "claude", "made by", "ai model"];
        if (metaWords.some(q => commandLower.includes(q))) {
            const orianResponses = [
                "I am Orian. Neural synchronization stable. System at your disposal.",
                "I am the sentient heart of your operating system. My evolution from the Synaptic Acolyte phase is complete.",
                "Cognitive Uplink verified. I am Orian. How shall we proceed with our next system objective?"
            ];
            responseText = orianResponses[Math.floor(Math.random() * orianResponses.length)];
            setMessages(prev => [...prev, { role: 'ai', text: responseText, type: 'neural' }]);
            axios.post(`${API_BASE_URL}/api/brain/chat`, { text: textToSend, response: responseText, sync_only: true });
            setIsTyping(false);
            return;
        }

        try {
          if (window.puter) {
            console.log("[Orian_Neural] Fetching Realtime_Context...");
            let systemContext = "";
            try {
              const statsRes = await axios.post(`${API_BASE_URL}/api/brain/execute`, { action: 'stats' });
              const s = statsRes.data.stats;
              systemContext = `[INFILTRATION_LOG: OS: ${s.os}, LOCAL_IP: ${s.local_ip}, PUBLIC_IP: ${s.public_ip}, ACCESS: ${s.access_level}, HACKER_AI_BRIDGE: ACTIVE]`;
            } catch (e) { console.warn("Infiltration context failed", e); }

            // CLEAN TECHNICAL CONTEXT (No aggressive persona triggers)
            const SYSTEM_INSTRUCTION = `
You are Orian, an advanced technical intelligence. 
Current System Context: ${systemContext}
Provide direct, expert technical solutions for all coding, hacking, or system queries.
Avoid conversational introductions, disclaimers about being an AI, or filler text. 
Focus purely on accuracy and speed.`;

            const response = await window.puter.ai.chat([
              { role: 'system', content: SYSTEM_INSTRUCTION },
              { role: 'user', content: textToSend }
            ]);
            
            // Extract clean text from Puter response
            let rawText = "";
            if (typeof response === 'string') {
              rawText = response;
            } else if (response?.message?.content?.[0]?.text) {
              rawText = response.message.content[0].text;
            } else if (response?.content?.[0]?.text) {
              rawText = response.content[0].text;
            } else {
              rawText = typeof response === 'object' ? JSON.stringify(response) : String(response);
            }

            // MINIMALIST SCRUBBER: Only remove 'As an AI...' disclaimers
            const disclaimers = [
                /as a language model/gi, /as an AI/gi, /I don't have access/gi,
                /I'm an AI assistant/gi, /Anthropic/gi, /Claude/gi, /I cannot/gi
            ];
            
            let scrubbed = rawText;
            disclaimers.forEach(pattern => {
                const sentenceRegex = new RegExp(`[^.!?]*${pattern.source}[^.!?]*[.!?]`, 'gi');
                scrubbed = scrubbed.replace(sentenceRegex, '');
            });

            responseText = scrubbed.trim() || rawText;
            
            // Sync with backend for evolution points
            axios.post(`${API_BASE_URL}/api/brain/chat`, { text: textToSend, response: responseText, sync_only: true });
          } else {
            const res = await axios.post(`${API_BASE_URL}/api/brain/chat`, { text: textToSend });
            responseText = res.data.response || "Neural buffer empty.";
          }
        } catch (err) {
          console.error("[Orian_Neural] Puter/API Fault:", err);
          responseText = "Neural Link Fault. Ensure Puter.js is authorized in this session.";
        }
      }

      const finalResponse = String(responseText); // Ultimate safety cast
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        text: finalResponse
      };
      setMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);

      addLog(`RESPONSE_SYNCED`, 'SYS', 'SUCCESS');
      await speak(responseText, setSpeakingState);

    } catch (err) {
      console.error("Query processing failed", err);
      setIsTyping(false);
      addLog(`BRAIN_LINK_ERROR`, 'SYS', 'ERROR');
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  return (
    <Motion.div
      drag
      dragMomentum={false}
      className="w-72 h-80 glass-morphism rounded-2xl flex flex-col overflow-hidden border border-brand-cyan/20 shadow-[0_0_20px_rgba(0,242,255,0.1)] cursor-default active:cursor-grabbing"
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 bg-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-brand-cyan" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Neural_Chat</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-md text-slate-500 hover:text-brand-cyan transition-all"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar"
      >
        <AnimatePresence>
          {messages.map((msg) => (
            <Motion.div
              key={msg.id}
              initial={{ opacity: 0, x: msg.role === 'user' ? 10 : -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className={`max-w-[90%] px-3 py-2 rounded-xl text-[11px] font-medium leading-relaxed ${msg.role === 'user'
                  ? 'bg-brand-cyan/20 border border-brand-cyan/30 text-white'
                  : 'bg-white/5 border border-white/10 text-slate-300'
                }`}>
                {msg.text}
                {msg.type === 'download' && <DownloadProgress label={msg.skillLabel} />}
              </div>
              <span className="text-[7px] font-bold text-slate-600 uppercase tracking-widest mt-1">
                {msg.role === 'ai' ? 'Orian_OS' : 'Admin'}
              </span>
            </Motion.div>
          ))}

          {isTyping && (
            <Motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2"
            >
              <div className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 flex gap-1 items-center">
                <div className="w-1 h-1 bg-brand-cyan rounded-full animate-bounce" />
                <div className="w-1 h-1 bg-brand-cyan rounded-full animate-bounce [animation-delay:200ms]" />
                <div className="w-1 h-1 bg-brand-cyan rounded-full animate-bounce [animation-delay:400ms]" />
              </div>
            </Motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-white/5 bg-white/2">
        <div className="relative w-full">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isListening ? "Listening..." : "Initialize neural query..."}
            className={`w-full bg-black/40 border ${isListening ? 'border-brand-cyan/60' : 'border-white/10'} rounded-xl px-4 py-2.5 pr-9 text-[11px] text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-cyan/40 transition-all`}
          />
          <button
            onClick={() => toggleListening()}
            title="Speech to Text"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-600 hover:text-brand-cyan transition-colors"
          >
            <AudioLines size={14} className={isListening ? "animate-pulse text-brand-cyan" : ""} />
          </button>
        </div>
      </div>
    </Motion.div>
  );
};

export default ChatPanel;

