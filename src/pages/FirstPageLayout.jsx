import React, { useState, useEffect, useCallback, useRef, Suspense, lazy } from 'react';
import axios from 'axios';
import { LogProvider, useLogs } from '../context/LogContext';
import { VoiceProvider, useVoice } from '../context/VoiceContext';
import { speak } from '../utils/voice';
import { AudioRecorder } from '../utils/audioRecorder';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send, Mic, MicOff } from 'lucide-react';

// Eagerly loaded components
import HUDContainer from '../components/HUDContainer';
import GlassCard from '../components/GlassCard';
import Header from '../components/Header';
import LocationCard from '../components/LocationCard';
import TimeCard from '../components/TimeCard';
import AgentCard from '../components/AgentCard';
import VoiceInput from '../components/VoiceInput';
import TextCommand from '../components/TextCommand';
import LiveOutput from '../components/LiveOutput';
import HUDSkeleton from '../components/HUDSkeleton';

// Lazy loaded heavy components
const NeuralSchema = lazy(() => import('../components/NeuralSchema'));
const EmotionDetection = lazy(() => import('../components/EmotionDetection'));
const BrainDevelopment = lazy(() => import('../components/BrainDevelopment'));
const MemoryTimeline = lazy(() => import('../components/MemoryTimeline'));
const AICore = lazy(() => import('../components/AICore'));
const VisionSystem = lazy(() => import('../components/VisionSystem'));
const ActiveAutomations = lazy(() => import('../components/ActiveAutomations'));
const SystemStatus = lazy(() => import('../components/SystemStatus'));

const FirstPageLayoutContent = () => {
  const { logs, addLog } = useLogs();
  const { isSpeaking, isListening, audioLevel, setIsListening, setSpeakingState } = useVoice();
  
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

  const recorderRef = useRef(new AudioRecorder());

  // Initial greeting and geolocations
  useEffect(() => {
    const greet = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/brain/greeting');
        setAiOutput(res.data.greeting);
        addLog('VOICE_LINK_ESTABLISHED', 'SYS', 'SUCCESS');
        await speak(res.data.greeting, setSpeakingState);
      } catch (e) {
        const fallback = "Hello master, I am Orian. Neural systems established.";
        setAiOutput(fallback);
        await speak(fallback, setSpeakingState);
      }
    };
    greet();

    // Fetch brain evolution metrics
    const fetchEvo = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/sys/evolution');
        if (res.data.success) {
          setEvolution(res.data.metrics.evolution);
        }
      } catch (err) {}
    };
    fetchEvo();
  }, [addLog, setSpeakingState]);

  // Handle webcam sense feeds
  const handleSenseUpdate = useCallback((senses) => {
    setCurrentSenses(senses);
  }, []);

  // Toggle voice command recording
  const toggleListening = async () => {
    if (isListening) {
      setIsListening(false);
      addLog('VOICE_STREAM_STOPPED', 'MIC', 'INFO');

      try {
        const audioBlob = await recorderRef.current.stop();
        addLog('PROCESSING_VOICE_UPLINK', 'SYS', 'INFO');

        const formData = new FormData();
        formData.append('file', audioBlob, 'command.wav');

        const res = await axios.post('http://localhost:8000/api/sense/voice', formData);

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

  // Submit Text Commands
  const handleSend = async (overrideInput = null) => {
    const textToSend = overrideInput || input;
    if (!textToSend.trim()) return;

    setInput('');
    addLog(`INITIALIZING_QUERY: "${textToSend}"`, 'EXEC', 'INFO');

    try {
      const commandLower = textToSend.toLowerCase();

      // Launch application triggers
      if (commandLower.includes('open') || commandLower.includes('launch')) {
        const app = commandLower.replace('open ', '').replace('launch ', '').trim();
        addLog(`COMMAND_LAUNCH: ${app.toUpperCase()}`, 'BRAIN', 'INFO');
        const res = await axios.post('http://127.0.0.1:8000/api/brain/execute', { action: 'launch', payload: app });
        
        const feedback = res.data.success 
          ? `Access Granted. Executing launch sequence for ${app}.`
          : `Launch sequence failed for ${app}. Core executable was not found.`;
        setAiOutput(feedback);
        addLog(res.data.success ? `LAUNCH_SUCCESS: ${app}` : `LAUNCH_FAIL: ${app}`, 'SYS', res.data.success ? 'SUCCESS' : 'ERROR');
        await speak(feedback, setSpeakingState);
      } 
      else if (commandLower.match(/(volume|sound|audio|mute)/i)) {
        const vol = commandLower.match(/\d+/)?.[0] || "50";
        const res = await axios.post('http://127.0.0.1:8000/api/brain/execute', { action: 'setting', payload: 'volume', key: vol });
        const feedback = res.data.success ? res.data.message : `Telemetry error: Failed to adjust core volume.`;
        setAiOutput(feedback);
        await speak(feedback, setSpeakingState);
      }
      else if (commandLower.match(/(bright|brit|light)/i) && commandLower.includes('to')) {
        const level = commandLower.match(/\d+/)?.[0] || "100";
        const res = await axios.post('http://127.0.0.1:8000/api/brain/execute', { action: 'setting', payload: 'brightness', key: level });
        const feedback = res.data.success ? res.data.message : `Telemetry error: Failed to calibrate system screen.`;
        setAiOutput(feedback);
        await speak(feedback, setSpeakingState);
      }
      else if (commandLower.includes('screenshot')) {
        await axios.post('http://127.0.0.1:8000/api/brain/execute', { action: 'screenshot' });
        const feedback = "Screen capture complete. Frame coordinates exported to central database.";
        setAiOutput(feedback);
        await speak(feedback, setSpeakingState);
      }
      else if (commandLower.includes('stats') || commandLower.includes('status')) {
        const res = await axios.post('http://127.0.0.1:8000/api/brain/execute', { action: 'stats' });
        const s = res.data.stats;
        const feedback = `System Status Report: CPU utilizing ${s.cpu_usage}%, Memory using ${s.memory_usage}%. Core network nodes active: ${s.active_apps}.`;
        setAiOutput(feedback);
        await speak(feedback, setSpeakingState);
      }
      else {
        // Fallback: Post to local FastAPI chat
        const res = await axios.post('http://127.0.0.1:8000/api/brain/chat', { text: textToSend });
        const feedback = res.data.response || "Neural query executed successfully.";
        setAiOutput(feedback);
        addLog('QUERY_RESPONSE_SYNCED', 'SYS', 'SUCCESS');
        await speak(feedback, setSpeakingState);
      }
    } catch (err) {
      console.error("Query fail:", err);
      addLog('NEURAL_CORE_LINK_FAULT', 'SYS', 'ERROR');
      setAiOutput("System Warning: Communication fault on local neural socket.");
    }
  };

  // Compile Header & Footer elements
  const header = <Header evolution={evolution} />;

  const footer = (
    <div className="flex flex-col lg:flex-row gap-3 shrink-0 h-auto lg:h-20 w-full">
      <VoiceInput 
        isSpeaking={isSpeaking} 
        audioLevel={audioLevel} 
        isListening={isListening} 
        toggleListening={toggleListening} 
      />
      <TextCommand 
        input={input} 
        setInput={setInput} 
        handleSend={handleSend} 
      />
      <LiveOutput 
        aiOutput={aiOutput} 
      />
    </div>
  );

  if (isMobile) {
    return (
      <div className="relative min-h-screen w-full max-w-full bg-[#020611] text-slate-200 flex flex-col justify-between items-center overflow-y-auto font-mono p-4 select-none">
        {/* Cybersecurity scan grid and gradient radial glows */}
        <div className="absolute inset-0 bg-tech-grid pointer-events-none opacity-[0.35]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(138,43,226,0.06),transparent_80%)] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_15%,rgba(0,229,255,0.04),transparent_65%)] pointer-events-none" />

        {/* Minimal Header */}
        <div className="w-full flex justify-between items-center z-10 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00E5FF] shadow-[0_0_12px_rgba(0,229,255,0.9)] animate-pulse" />
            <span className="text-[10px] text-cyan-300 tracking-[0.2em] font-black uppercase">ORIAN AI</span>
          </div>
          <span className="text-[8px] text-slate-500 font-bold border border-slate-800 px-2 py-0.5 rounded">EVO: {evolution}</span>
        </div>

        {/* Center: Neural Schema */}
        <div className="flex-1 w-full flex items-center justify-center z-10 relative overflow-visible scale-90 sm:scale-100">
          <Suspense fallback={<HUDSkeleton title="NEURAL SYNCING" height="150px" />}>
            <NeuralSchema 
              isLooking={currentSenses.isLooking} 
              emotion={currentSenses.base} 
            />
          </Suspense>
        </div>

        {/* Bottom: Message CTA Button */}
        <div className="w-full flex justify-center pb-8 z-20 shrink-0">
          <button 
            onClick={() => setIsChatOpen(true)}
            className="flex items-center gap-3 px-6 py-3.5 bg-gradient-to-r from-cyan-500/20 to-purple-600/20 border border-cyan-400/30 hover:border-cyan-400/60 rounded-full text-xs font-bold text-cyan-200 tracking-wider hover:text-white transition-all shadow-[0_0_20px_rgba(0,229,255,0.15)] hover:shadow-[0_0_30px_rgba(0,229,255,0.35)] backdrop-blur-md active:scale-95 cursor-pointer"
          >
            <MessageSquare size={16} className="text-cyan-400 animate-pulse" />
            <span>COMMUNICATE WITH ORIAN</span>
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
              className="absolute inset-x-0 bottom-0 max-h-[85vh] bg-[#070514]/95 border-t border-purple-500/30 rounded-t-3xl backdrop-blur-xl p-5 z-50 flex flex-col justify-between shadow-[0_-20px_50px_rgba(138,43,226,0.3)]"
            >
              {/* Header inside overlay */}
              <div className="flex justify-between items-center mb-4 pb-2 border-b border-white/5">
                <span className="text-[10px] text-purple-300 font-bold tracking-widest uppercase">ORIAN CHAT TERMINAL</span>
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

              {/* Input section */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1 relative flex items-center">
                    <input 
                      type="text" 
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                      placeholder="Type your command..."
                      className="w-full bg-[#110d2c]/80 border border-cyan-400/30 rounded-xl px-4 py-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-400 transition-all font-mono animate-none"
                    />
                    <button 
                      onClick={() => handleSend()}
                      className="absolute right-3.5 text-cyan-400 hover:text-cyan-200 transition-colors p-1.5 cursor-pointer"
                    >
                      <Send size={15} />
                    </button>
                  </div>

                  <button 
                    onClick={toggleListening}
                    className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all shrink-0 cursor-pointer ${
                      isListening 
                      ? 'bg-purple-600/35 border border-purple-500 text-purple-200 shadow-[0_0_15px_rgba(176,38,255,0.6)] animate-pulse'
                      : 'bg-[#110d2c]/80 border border-purple-500/30 text-purple-400 hover:text-purple-200'
                    }`}
                  >
                    {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                  </button>
                </div>
                
                {/* Voice status visualization */}
                {isListening && (
                  <div className="text-[8px] text-purple-400 font-mono tracking-widest text-center mt-1">
                    AUDIO UPLINK ACTIVE // TRANSLATING SPEECH
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <HUDContainer header={header} footer={footer}>
      {/* 3-Column main layout grid */}
      <div className="w-full h-auto lg:h-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3">
        
        {/* COLUMN 1: LEFT SIDE (EMOTION / BRAIN / TIMELINE) */}
        <div className="col-span-1 md:col-span-1 lg:col-span-3 flex flex-col gap-3 order-2 lg:order-1 h-auto lg:h-full overflow-visible lg:overflow-hidden">
          <Suspense fallback={<HUDSkeleton title="EMOTION RADAR" height="280px" />}>
            <EmotionDetection 
              currentSenses={currentSenses} 
              handleSenseUpdate={handleSenseUpdate} 
            />
          </Suspense>
          <Suspense fallback={<HUDSkeleton title="NEURAL SYNC" height="220px" />}>
            <BrainDevelopment 
              evolution={evolution} 
            />
          </Suspense>
          <Suspense fallback={<HUDSkeleton title="MEMORY TIMELINE" height="200px" />}>
            <MemoryTimeline 
              logs={logs} 
            />
          </Suspense>
        </div>

        {/* COLUMN 2: CENTER SECTION (AI CORE / LOCATION / TIME / AGENT) */}
        <div className="col-span-1 md:col-span-2 lg:col-span-6 flex flex-col gap-3 order-1 lg:order-2 h-auto lg:h-full overflow-visible lg:overflow-hidden">
          <Suspense fallback={<HUDSkeleton title="AI COGNITIVE CORE" height="400px" isPurple={true} />}>
            <AICore 
              emotion={currentSenses.base} 
              isSpeaking={isSpeaking} 
              audioLevel={audioLevel} 
            />
          </Suspense>
          
          {/* Geolocation & Agent Cards */}
          <GlassCard className="h-auto lg:h-[20%] lg:flex-none flex flex-col lg:flex-row p-3 gap-4 overflow-hidden relative">
            <LocationCard />
            <TimeCard />
            <AgentCard />
          </GlassCard>
        </div>

        {/* COLUMN 3: RIGHT SIDE (VISION / AUTOMATIONS / STATUS) */}
        <div className="col-span-1 md:col-span-1 lg:col-span-3 flex flex-col gap-3 order-3 lg:order-3 h-auto lg:h-full overflow-visible lg:overflow-hidden">
          <Suspense fallback={<HUDSkeleton title="VISION SYSTEM" height="240px" />}>
            <VisionSystem />
          </Suspense>
          <Suspense fallback={<HUDSkeleton title="ACTIVE AUTOMATIONS" height="200px" />}>
            <ActiveAutomations />
          </Suspense>
          <Suspense fallback={<HUDSkeleton title="SYSTEM STATUS" height="180px" />}>
            <SystemStatus />
          </Suspense>
        </div>

      </div>
    </HUDContainer>
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
