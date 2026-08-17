import React, { useState, useEffect, useCallback, useRef, Suspense, lazy } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { LogProvider, useLogs } from '../context/LogContext';
import { VoiceProvider, useVoice } from '../context/VoiceContext';
import { speak, unlockAudio } from '../utils/voice';
import { playSuccessChime, playMicActivate } from '../utils/sound';
import { AudioRecorder } from '../utils/audioRecorder';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, AudioLines, Volume2 } from 'lucide-react';
import WakeWordListener from '../mobile/WakeWordListener';

// Eagerly loaded components from features
import { HUDContainer, GlassCard, Header, LiveOutput, HUDSkeleton, NotificationToastSystem } from '../features/ui';
import { VoiceInput, TextCommand } from '../features/chat';
import { LiveTaskDashboard } from '../features/tasks';
import { useTaskOrchestrator } from '../hooks/useTaskOrchestrator';

// Lazy-loaded feature components
const NeuralSchema = lazy(() => import('../features/brain/NeuralSchema'));
const CircularCore = lazy(() => import('../features/brain/CircularCore'));
const EmotionDetection = lazy(() => import('../features/senses/EmotionDetection'));
const MemoryTimeline = lazy(() => import('../features/tasks/MemoryTimeline'));
const AICore = lazy(() => import('../features/brain/AICore'));
const ActiveAutomations = lazy(() => import('../features/tasks/ActiveAutomations'));
const SystemStatus = lazy(() => import('../features/system/SystemStatus'));



const FirstPageLayoutContent = () => {
  const { logs, addLog } = useLogs();
  const { isSpeaking, isListening, audioLevel, setIsListening, setSpeakingState, registerSpeechEndCallback } = useVoice();
  const { tasks, toasts, stats, isConnected, dispatchPrompt, cancelTask, retryTask, removeToast } = useTaskOrchestrator();
  
  const [currentSenses, setCurrentSenses] = useState({
    emotion: 'NEUTRAL',
    base: 'neutral',
    isLooking: false,
    faceCenter: { x: 0.5, y: 0.5 },
    spatial: { azimuth: 0, distance: 0.6 }
  });

  
  const [input, setInput] = useState('');
  const [aiOutput, setAiOutput] = useState('ORIAN AI OS initialized. All neural cores synced.');
  const [evolution, setEvolution] = useState('68.4%');
  const [onlineAgents, setOnlineAgents] = useState(6);
  const [isMobile, setIsMobile] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Listen to agent online greetings and sync directly into Live AI Output
  useEffect(() => {
    const handleAgentOnlineEvent = (e) => {
      const { message, agentName } = e.detail || {};
      const greetingMsg = message || (agentName ? `${agentName.toLowerCase()} agent is online` : "titan ai orchestrator agent is online");
      if (greetingMsg) {
        setAiOutput(greetingMsg);
        addLog(`AGENT_ONLINE_SYNC: ${greetingMsg.toUpperCase()}`, 'BRAIN', 'SUCCESS');
      }
    };

    window.addEventListener('orian-agent-online', handleAgentOnlineEvent);
    return () => window.removeEventListener('orian-agent-online', handleAgentOnlineEvent);
  }, [addLog]);

  const recorderRef = useRef(new AudioRecorder());
  const greetedRef = useRef(false);
  const autoListenRef = useRef(true);
  const recognitionRef = useRef(null);
  const isSendingRef = useRef(false);
  const lastSentTimeRef = useRef(0);
  const lastSentPromptRef = useRef('');

  // VAD Speech Recognition / Hands-Free Loop Trigger
  const startVADListening = useCallback(() => {
    if (!autoListenRef.current) return;
    const SpeechRecognition = typeof window !== 'undefined' ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
    
    if (SpeechRecognition) {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }
      const rec = new SpeechRecognition();
      recognitionRef.current = rec;
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'en-US';

      let finalTranscript = '';

      rec.onstart = () => {
        setIsListening(true);
        addLog('VAD_LISTENING_ACTIVE', 'MIC', 'INFO');
      };

      rec.onresult = (event) => {
        let currentInterim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            currentInterim += transcript;
          }
        }
        const textSoFar = finalTranscript || currentInterim;
        if (textSoFar.trim()) {
          setInput(textSoFar);
        }
      };

      rec.onerror = (event) => {
        console.warn("VAD speech recognition error:", event.error);
        setIsListening(false);
        if (autoListenRef.current && (event.error === 'no-speech' || event.error === 'aborted' || event.error === 'network')) {
          setTimeout(() => {
            if (autoListenRef.current) startVADListening();
          }, 600);
        }
      };

      rec.onend = () => {
        setIsListening(false);
        if (finalTranscript.trim()) {
          const textToProcess = finalTranscript.trim();
          setInput('');
          handleSend(textToProcess);
        } else if (autoListenRef.current) {
          setTimeout(() => {
            if (autoListenRef.current) startVADListening();
          }, 500);
        }
      };

      try {
        rec.start();
      } catch (err) {
        console.warn("SpeechRecognition start fault:", err);
        setIsListening(false);
      }
    } else {
      toggleListening();
    }
  }, [setIsListening, addLog]);

  const pendingGreetingRef = useRef('');
  const hasSpokenGreetingRef = useRef(false);

  const speakGreeting = useCallback(async (text) => {
    const textToSpeak = text || pendingGreetingRef.current || aiOutput;
    if (!textToSpeak) return;
    try {
      unlockAudio();
      hasSpokenGreetingRef.current = true;
      await speak(textToSpeak, setSpeakingState);
    } catch (e) {
      console.warn("Greeting voice output fault:", e);
    }
  }, [aiOutput, setSpeakingState]);


  // Initial greeting & mobile/desktop user interaction listener
  useEffect(() => {
    const enableAudioAndListen = () => {
      autoListenRef.current = true;
      unlockAudio();
      if (!hasSpokenGreetingRef.current && pendingGreetingRef.current) {
        speakGreeting(pendingGreetingRef.current);
      }
    };

    // Listen to touch events for mobile touchscreens (iOS Safari, Android Chrome, WebViews)
    window.addEventListener('touchstart', enableAudioAndListen, { once: true, passive: true });
    window.addEventListener('touchend', enableAudioAndListen, { once: true, passive: true });
    window.addEventListener('pointerdown', enableAudioAndListen, { once: true, passive: true });
    window.addEventListener('click', enableAudioAndListen, { once: true });
    window.addEventListener('keydown', enableAudioAndListen, { once: true });

    if (!greetedRef.current) {
      greetedRef.current = true;

      const greet = async () => {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/brain/greeting`);
          const msg = res.data.greeting || "Hello master, I am Orian. Neural link established.";
          setAiOutput(msg);
          pendingGreetingRef.current = msg;
          addLog('VOICE_LINK_ESTABLISHED', 'SYS', 'SUCCESS');
          
          try {
            await speak(msg, (speaking, audio) => {
              setSpeakingState(speaking, audio);
              if (speaking) hasSpokenGreetingRef.current = true;
            });
          } catch (err) {
            console.warn("Initial autoplay blocked on mobile, will play upon first touch/tap");
          }
        } catch (e) {
          const fallback = "Hello master, I am Orian. Neural systems established.";
          setAiOutput(fallback);
          pendingGreetingRef.current = fallback;
          try {
            await speak(fallback, (speaking, audio) => {
              setSpeakingState(speaking, audio);
              if (speaking) hasSpokenGreetingRef.current = true;
            });
          } catch (err) {}
        }
      };
      greet();
    }

    return () => {
      window.removeEventListener('touchstart', enableAudioAndListen);
      window.removeEventListener('touchend', enableAudioAndListen);
      window.removeEventListener('pointerdown', enableAudioAndListen);
      window.removeEventListener('click', enableAudioAndListen);
      window.removeEventListener('keydown', enableAudioAndListen);
    };
  }, [setSpeakingState, addLog, speakGreeting]);

  // Dedicated Real-Time Brain Evolution & AI Agents Sync Hook
  useEffect(() => {
    let isMounted = true;
    const fetchEvo = async () => {
      try {
        let res;
        const urls = [
          `${API_BASE_URL}/api/sys/evolution`,
          'http://127.0.0.1:8000/api/sys/evolution',
          'http://localhost:8000/api/sys/evolution'
        ].filter(Boolean);

        for (const url of urls) {
          try {
            res = await axios.get(url, { timeout: 2000 });
            if (res.data && res.data.success) break;
          } catch (e) {
            continue;
          }
        }

        if (isMounted && res && res.data && res.data.success && res.data.metrics) {
          if (res.data.metrics.evolution) {
            setEvolution(res.data.metrics.evolution);
          }
          if (res.data.metrics.online_agents !== undefined) {
            setOnlineAgents(res.data.metrics.online_agents);
          }
        }
      } catch (err) {
        console.warn('[RealTimeSync] Evolution query error:', err.message);
      }
    };

    fetchEvo();
    const evoInterval = setInterval(fetchEvo, 2000);

    return () => {
      isMounted = false;
      clearInterval(evoInterval);
    };
  }, []);

  // Handle webcam sense feeds
  const handleSenseUpdate = useCallback((senses) => {
    setCurrentSenses(senses);
  }, []);

  const handleWake = useCallback(() => {
    unlockAudio();
    playMicActivate();
    addLog('WAKE_WORD_SPOTTED: "HELLO ORIAN"', 'BRAIN', 'SUCCESS');
    setIsChatOpen(true);
    autoListenRef.current = true;
    startVADListening();
  }, [addLog, startVADListening]);

  const handleCtaClick = useCallback(() => {
    unlockAudio();
    playSuccessChime();
    setIsChatOpen(prev => !prev);
    const triggerBtn = document.getElementById('wake-word-permission-trigger');
    if (triggerBtn) triggerBtn.click();
  }, []);

  // Toggle voice command recording (fallback method)
  const toggleListening = async () => {
    if (isListening) {
      setIsListening(false);
      addLog('VOICE_STREAM_STOPPED', 'MIC', 'INFO');

      try {
        const audioBlob = await recorderRef.current.stop();
        addLog('PROCESSING_VOICE_UPLINK', 'SYS', 'INFO');

        const formData = new FormData();
        formData.append('file', audioBlob, 'command.wav');

        const res = await axios.post(`${API_BASE_URL}/api/sense/voice`, formData);

        if (res.data.success) {
          const transcript = res.data.transcript;
          addLog(`SPEECH_RECOGNIZED: "${transcript}"`, 'BRAIN', 'SUCCESS');
          handleSend(transcript);
        } else {
          addLog(`VOICE_STT_ERROR: ${res.data.message}`, 'BRAIN', 'ERROR');
        }
      } catch (err) {
        addLog('AUDIO_MIC_SYNC_FAULT', 'SYS', 'ERROR');
      }
    } else {
      try {
        await recorderRef.current.start();
        setIsListening(true);
        addLog('VOICE_MIC_UPLINK_ESTABLISHED', 'MIC', 'SUCCESS');
      } catch (err) {
        addLog('MIC_HARDWARE_NOT_READY', 'SYS', 'ERROR');
      }
    }
  };

  // Submit Commands & Desktop Actions
  const handleSend = async (overrideInput = null) => {
    const textToSend = (overrideInput || input || '').trim();
    if (!textToSend) return;

    const now = Date.now();
    // Guard against rapid duplicate submissions (within 1.5 seconds)
    if (isSendingRef.current || (lastSentPromptRef.current.toLowerCase() === textToSend.toLowerCase() && now - lastSentTimeRef.current < 1500)) {
      return;
    }

    isSendingRef.current = true;
    lastSentTimeRef.current = now;
    lastSentPromptRef.current = textToSend;

    setInput('');
    addLog(`INITIALIZING_QUERY: "${textToSend}"`, 'EXEC', 'INFO');

    try {
      // 1. Dispatch prompt to Autonomous Task Orchestrator & LLM Planner
      const dispatchRes = await dispatchPrompt(textToSend);
      
      let feedback = "";
      if (dispatchRes && (dispatchRes.response || dispatchRes.message)) {
        feedback = dispatchRes.response || dispatchRes.message;
      } else if (dispatchRes && dispatchRes.count > 0) {
        feedback = `Right away. Dispatched ${dispatchRes.count} action${dispatchRes.count > 1 ? 's' : ''} in real time.`;
      } else {
        let chatRes;
        const urls = [
          `${API_BASE_URL}/api/brain/chat`,
          'http://127.0.0.1:8000/api/brain/chat',
          'http://localhost:8000/api/brain/chat'
        ].filter(Boolean);

        for (const url of urls) {
          try {
            chatRes = await axios.post(url, { text: textToSend }, { timeout: 5000 });
            if (chatRes.data && chatRes.data.success) break;
          } catch (e) {
            continue;
          }
        }
        feedback = chatRes?.data?.response || "Neural query executed successfully.";
      }

      setAiOutput(feedback);
      addLog('QUERY_RESPONSE_SYNCED', 'SYS', 'SUCCESS');

      // Speak Jarvis immediate acknowledgment
      await speak(feedback, setSpeakingState);

      // Hands-free continuous loop resumption
      if (autoListenRef.current) {
        startVADListening();
      }
    } catch (err) {
      addLog(`QUERY_EXEC_FAULT: ${err.message}`, 'EXEC', 'ERROR');
    } finally {
      setTimeout(() => {
        isSendingRef.current = false;
      }, 500);
    }
  };


  // Compile Header & Footer elements
  const header = <Header evolution={evolution} onlineAgents={onlineAgents} />;

  const footer = (
    <div className="flex flex-col lg:flex-row gap-3 shrink-0 h-auto lg:h-20 w-full">
      <VoiceInput 
        isSpeaking={isSpeaking} 
        audioLevel={audioLevel} 
        isListening={isListening} 
      />
      <TextCommand 
        input={input} 
        setInput={setInput} 
        handleSend={handleSend} 
        isListening={isListening}
        toggleSTT={startVADListening}
      />
      <LiveOutput 
        aiOutput={aiOutput} 
      />
    </div>
  );

  if (isMobile) {
    return (
      <>
        <div className="relative min-h-[100dvh] h-[100dvh] w-full max-w-full bg-[#020611] text-slate-200 flex flex-col justify-between items-center overflow-hidden font-mono p-4 select-none">
          {/* Cybersecurity scan grid and gradient radial glows */}
          <div className="absolute inset-0 bg-tech-grid pointer-events-none opacity-[0.35] z-0" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(0,102,255,0.06),transparent_80%)] pointer-events-none z-0" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_15%,rgba(0,229,255,0.04),transparent_65%)] pointer-events-none z-0" />

          {/* Full Screen Neural Schema Background */}
          <div className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none opacity-60 overflow-hidden scale-[1.1] sm:scale-[1.25]">
            <Suspense fallback={null}>
              <CircularCore 
                emotion={currentSenses.base} 
                isSpeaking={isSpeaking} 
                isListening={isListening}
                audioLevel={audioLevel} 
              />
            </Suspense>
          </div>

          {/* Minimal Header */}
          <div className="w-full flex justify-between items-center z-10 shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00E5FF] shadow-[0_0_12px_rgba(0,229,255,0.9)] animate-pulse" />
              <span className="text-[10px] text-cyan-300 tracking-[0.2em] font-black uppercase">ORIAN AI</span>
            </div>
            <span className="text-[8px] text-slate-500 font-bold border border-slate-800 px-2 py-0.5 rounded">EVO: {evolution}</span>
          </div>

          {/* Center Mobile Voice & Greeting Trigger */}
          <div className="z-20 flex flex-col items-center gap-3 my-auto max-w-[90%] text-center">
            <button
              onClick={() => {
                unlockAudio();
                playSuccessChime();
                speakGreeting();
              }}
              title="Hear Greeting Voice"
              aria-label="Hear Greeting Voice"
              className="flex items-center gap-2.5 px-5 py-3 rounded-full bg-cyan-500/15 border border-cyan-400/40 text-cyan-200 backdrop-blur-xl active:scale-95 transition-all shadow-[0_0_25px_rgba(0,229,255,0.25)] hover:bg-cyan-500/25 cursor-pointer min-h-[48px] touch-target group"
            >
              <Volume2 size={18} className={isSpeaking ? "animate-pulse text-cyan-200" : "text-cyan-400 group-hover:scale-110 transition-transform"} />
              <span className="text-xs font-bold tracking-wider uppercase">
                {isSpeaking ? "Orian Speaking..." : "Play Voice Greeting"}
              </span>
            </button>
            <div className="text-[10px] text-slate-400 font-mono line-clamp-3 max-w-xs bg-black/40 border border-white/5 rounded-xl px-3 py-1.5 backdrop-blur-md">
              {aiOutput}
            </div>
          </div>

          {/* Bottom Right: Circular CTA Button */}
          <div className="fixed bottom-6 right-6 z-40">
            <button 
              onClick={handleCtaClick}
              className="w-14 h-14 rounded-full flex items-center justify-center bg-gradient-to-tr from-cyan-500/30 to-blue-600/30 border border-cyan-400/40 hover:border-cyan-400/70 text-cyan-200 shadow-[0_0_20px_rgba(0,102,255,0.3)] hover:shadow-[0_0_30px_rgba(0,102,255,0.6)] backdrop-blur-md active:scale-95 cursor-pointer transition-all duration-300 group"
            >
              <MessageSquare size={22} className="text-cyan-400 group-hover:scale-110 transition-transform animate-pulse" />
            </button>
          </div>

          {/* Slide-up Chat Overlay */}
          <AnimatePresence>
            {isChatOpen && (
              <motion.div 
                initial={{ opacity: 0, y: '100%' }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="absolute inset-x-0 bottom-0 max-h-[85vh] bg-[#020510]/95 border-t border-blue-500/35 rounded-t-3xl backdrop-blur-xl p-5 z-50 flex flex-col justify-between shadow-[0_-15px_40px_rgba(0,102,255,0.25)]"
              >
                {/* Header inside overlay */}
                <div className="flex justify-between items-center mb-4 pb-2 border-b border-white/5">
                  <span className="text-[10px] text-cyan-300 font-bold tracking-widest uppercase">ORIAN CHAT TERMINAL</span>
                  <button 
                    onClick={() => setIsChatOpen(false)}
                    className="text-slate-400 hover:text-white transition-colors p-1 cursor-pointer"
                  >
                    <X size={18} />
                  </button>
                </div>

                {/* Chat history / output area */}
                <div className="flex-1 overflow-y-auto mb-4 min-h-[150px] flex flex-col justify-end bg-black/40 border border-white/5 rounded-xl p-4 gap-3">
                  <div className="text-[10px] text-slate-500 uppercase tracking-widest leading-normal">System Feed</div>
                  <div className="text-xs text-slate-300 bg-white/5 border border-white/5 p-3 rounded-lg leading-relaxed font-mono whitespace-pre-wrap">
                    {aiOutput || 'Core synced. Ready for instructions...'}
                  </div>
                  {isSpeaking && (
                    <div className="text-[9px] text-cyan-400 font-bold animate-pulse flex items-center gap-1.5 mt-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff]" />
                      Orian is speaking...
                    </div>
                  )}
                </div>

                {/* Input section Section */}
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 relative flex items-center">
                      <input 
                        type="text" 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder={isListening ? "Listening..." : "Type your command..."}
                        className="w-full bg-[#050B20]/90 border border-cyan-400/40 rounded-xl px-4 py-3.5 pr-12 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-400 transition-all font-mono min-h-[48px] shadow-[0_0_15px_rgba(0,229,255,0.1)]"
                      />
                      <button 
                        onClick={() => startVADListening()}
                        title="Speech to Text"
                        aria-label="Speech to Text"
                        className="absolute right-2 text-cyan-400 hover:text-cyan-200 transition-colors p-2.5 cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center"
                      >
                        <AudioLines size={18} className={isListening ? "animate-pulse text-cyan-200" : ""} />
                      </button>
                    </div>
                  </div>
                  
                  {/* Voice status visualization */}
                  {isListening && (
                    <div className="text-[8px] text-cyan-400 font-mono tracking-widest text-center mt-1">
                      AUDIO UPLINK ACTIVE // TRANSLATING SPEECH
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <WakeWordListener onWake={handleWake} />
      </>
    );
  }

  return (
    <>
      <HUDContainer header={header} footer={footer}>
        {/* 3-Column main layout grid */}
        <div className="w-full h-auto lg:h-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3 lg:gap-2.5">
          
          {/* COLUMN 1: LEFT SIDE (EMOTION / TIMELINE) */}
          <div className="col-span-1 md:col-span-1 lg:col-span-3 flex flex-col gap-3 lg:gap-2.5 order-2 lg:order-1 h-auto lg:h-full overflow-visible lg:overflow-hidden">
            <Suspense fallback={<HUDSkeleton title="EMOTION RADAR" height="280px" />}>
              <EmotionDetection 
                currentSenses={currentSenses} 
                handleSenseUpdate={handleSenseUpdate} 
              />
            </Suspense>
            <Suspense fallback={<HUDSkeleton title="MEMORY TIMELINE" height="200px" />}>
              <MemoryTimeline 
                logs={logs} 
              />
            </Suspense>
          </div>

          {/* COLUMN 2: CENTER SECTION (AI CORE / LOCATION / TIME / AGENT) */}
          <div className="col-span-1 md:col-span-2 lg:col-span-6 flex flex-col gap-3 lg:gap-2.5 order-1 lg:order-2 h-auto lg:h-full overflow-visible lg:overflow-hidden">
            <Suspense fallback={<HUDSkeleton title="AI COGNITIVE CORE" height="400px" isPurple={true} />}>
              <AICore 
                emotion={currentSenses.base} 
                isSpeaking={isSpeaking} 
                isListening={isListening}
                audioLevel={audioLevel} 
              />
            </Suspense>
            
          </div>

          {/* COLUMN 3: RIGHT SIDE (AUTOMATIONS / STATUS) */}
          <div className="col-span-1 md:col-span-1 lg:col-span-3 flex flex-col gap-3 lg:gap-2.5 order-3 lg:order-3 h-auto lg:h-full overflow-visible lg:overflow-hidden">
            <Suspense fallback={<HUDSkeleton title="ACTIVE AUTOMATIONS" height="200px" />}>
              <ActiveAutomations />
            </Suspense>
            <Suspense fallback={<HUDSkeleton title="SYSTEM STATUS" height="180px" />}>
              <SystemStatus />
            </Suspense>
          </div>


        </div>
      </HUDContainer>
      <NotificationToastSystem toasts={toasts} onRemove={removeToast} />
      <WakeWordListener onWake={handleWake} />
    </>
  );

};

const FirstPageLayout = () => (
  <LogProvider>
    <VoiceProvider>
      <FirstPageLayoutContent />
    </VoiceProvider>
  </LogProvider>
);

export default FirstPageLayout;
