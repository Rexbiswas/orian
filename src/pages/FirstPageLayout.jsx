import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { LogProvider, useLogs } from '../context/LogContext';
import { VoiceProvider, useVoice } from '../context/VoiceContext';
import { speak } from '../utils/voice';
import { AudioRecorder } from '../utils/audioRecorder';

// Import our modular HUD components
import HUDContainer from '../components/HUDContainer';
import GlassCard from '../components/GlassCard';
import Header from '../components/Header';
import EmotionDetection from '../components/EmotionDetection';
import BrainDevelopment from '../components/BrainDevelopment';
import MemoryTimeline from '../components/MemoryTimeline';
import AICore from '../components/AICore';
import LocationCard from '../components/LocationCard';
import TimeCard from '../components/TimeCard';
import AgentCard from '../components/AgentCard';
import VisionSystem from '../components/VisionSystem';
import ActiveAutomations from '../components/ActiveAutomations';
import SystemStatus from '../components/SystemStatus';
import VoiceInput from '../components/VoiceInput';
import TextCommand from '../components/TextCommand';
import LiveOutput from '../components/LiveOutput';

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

  return (
    <HUDContainer header={header} footer={footer}>
      {/* 3-Column main layout grid */}
      <div className="w-full h-auto lg:h-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3">
        
        {/* COLUMN 1: LEFT SIDE (EMOTION / BRAIN / TIMELINE) */}
        <div className="col-span-1 md:col-span-1 lg:col-span-3 flex flex-col gap-3 order-2 lg:order-1 h-auto lg:h-full overflow-visible lg:overflow-hidden">
          <EmotionDetection 
            currentSenses={currentSenses} 
            handleSenseUpdate={handleSenseUpdate} 
          />
          <BrainDevelopment 
            evolution={evolution} 
          />
          <MemoryTimeline 
            logs={logs} 
          />
        </div>

        {/* COLUMN 2: CENTER SECTION (AI CORE / LOCATION / TIME / AGENT) */}
        <div className="col-span-1 md:col-span-2 lg:col-span-6 flex flex-col gap-3 order-1 lg:order-2 h-auto lg:h-full overflow-visible lg:overflow-hidden">
          <AICore 
            emotion={currentSenses.base} 
            isSpeaking={isSpeaking} 
            audioLevel={audioLevel} 
          />
          
          {/* Geolocation & Agent Cards */}
          <GlassCard className="h-auto lg:h-[20%] lg:flex-none flex flex-col lg:flex-row p-3 gap-4 overflow-hidden relative">
            <LocationCard />
            <TimeCard />
            <AgentCard />
          </GlassCard>
        </div>

        {/* COLUMN 3: RIGHT SIDE (VISION / AUTOMATIONS / STATUS) */}
        <div className="col-span-1 md:col-span-1 lg:col-span-3 flex flex-col gap-3 order-3 lg:order-3 h-auto lg:h-full overflow-visible lg:overflow-hidden">
          <VisionSystem />
          <ActiveAutomations />
          <SystemStatus />
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
