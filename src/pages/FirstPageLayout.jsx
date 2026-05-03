import React, { useState, useEffect, useCallback } from 'react';
import Navbar from '../components/Navbar';
import NeuralSchema from '../components/NeuralSchema';
import AIPanel from '../components/AIPanel';
import ChatPanel from '../components/ChatPanel';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import NeuralLog from '../components/NeuralLog';
import HumanSenses from '../components/HumanSenses/HumanSenses';
import HackingSimulation from '../components/HackingSimulation';
import { LogProvider, useLogs } from '../context/LogContext';
import { VoiceProvider, useVoice } from '../context/VoiceContext';
import { MessageSquare, Activity, Shield } from 'lucide-react';
import { speak } from '../utils/voice';
import axios from 'axios';
import NeuralPulse from '../components/NeuralPulse';

const TriggerButton = ({ active, onClick, icon: Icon, color, activeColor }) => (
  <Motion.button
    whileHover={{ scale: 1.1, y: -2 }}
    whileTap={{ scale: 0.9 }}
    onClick={onClick}
    className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all overflow-hidden group pointer-events-auto border ${
      active 
      ? `${activeColor} border-current shadow-[0_0_30px_rgba(0,242,255,0.2)]` 
      : 'bg-slate-900/40 border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20'
    }`}
  >
    <Icon size={24} />
  </Motion.button>
);

const FirstPageLayoutContent = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isHackingOpen, setIsHackingOpen] = useState(false);
  const { isLogOpen, setIsLogOpen, addLog } = useLogs();
  const { setSpeakingState } = useVoice();
  const [hasGreeted, setHasGreeted] = useState(false);
  const [currentSenses, setCurrentSenses] = useState(null);

  const handleSenseUpdate = useCallback((senses) => {
    setCurrentSenses(senses);
    if (senses.emotion !== 'neutral' && senses.isLooking) {
      addLog(`USER_EMOTION_DETECTED: ${senses.emotion.toUpperCase()}`, 'AI_CORE', 'INFO');
    }
    if (!senses.isLooking && senses.isLooking !== currentSenses?.isLooking) {
      addLog('USER_ENGAGEMENT_DROPPED', 'AI_CORE', 'WARNING');
    }
  }, [addLog, currentSenses]);

  useEffect(() => {
    const triggerGreeting = async () => {
      if (hasGreeted) return;
      setHasGreeted(true);
      
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/brain/greeting');
        const greeting = res.data.greeting;
        addLog('VOICE_ENGINE_ACTIVATED', 'SYS', 'SUCCESS');
        await speak(greeting, setSpeakingState);
        addLog('NEURAL_PERSONALITY_SYNCED', 'BRAIN', 'INFO');
      } catch (err) {
        await speak("Hello master, I am Orian. Neural links established.", setSpeakingState);
      }
    };
    triggerGreeting();
  }, [hasGreeted, addLog, setSpeakingState]);

  const [evolution, setEvolution] = useState("0%");
  
  useEffect(() => {
    const fetchEvo = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/sys/evolution');
        setEvolution(res.data.metrics.evolution);
      } catch (e) {}
    };
    fetchEvo();
    const interval = setInterval(fetchEvo, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen w-screen bg-[#020617] text-slate-200 flex flex-col overflow-hidden relative font-sans">
      <Motion.div 
        animate={{ 
          backgroundPosition: ['0% 0%', '100% 100%'],
          opacity: [0.03, 0.06, 0.03]
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 bg-tech-grid pointer-events-none" 
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,242,255,0.05),transparent_70%)] pointer-events-none" />
      <Navbar />

      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Side Telemetry */}
        <div className="absolute top-12 left-12 flex flex-col gap-6 pointer-events-auto z-40">
           {[
             { label: "PROTOCOL", value: "GENESIS_OS", color: "text-brand-cyan" },
             { 
               label: "EYE_CONTACT", 
               value: currentSenses?.isLooking ? "ESTABLISHED" : "SCANNING", 
               color: currentSenses?.isLooking ? "text-emerald-400" : "text-slate-500" 
             },
             { 
               label: "FACIAL_LINK", 
               value: currentSenses?.emotion?.toUpperCase() || "SEARCHING...", 
               color: currentSenses?.emotion?.includes('HAPPY') ? 'text-emerald-400' : 
                      (currentSenses?.emotion?.includes('CALM') ? 'text-brand-cyan' : 
                      (currentSenses?.emotion?.includes('SURPRISED') ? 'text-yellow-400' : 'text-slate-500'))
             },
             { 
               label: "EMOTION_LINK", 
               value: currentSenses?.base?.toUpperCase() || "SEARCHING...", 
               color: currentSenses?.base === 'happy' ? 'text-emerald-400' : 
                      (currentSenses?.base === 'sad' ? 'text-blue-400' : 'text-brand-purple')
             },
             { 
               label: "BRAIN_EVO", 
               value: evolution, 
               color: "text-brand-purple" 
             }
           ].map((item, i) => (
             <Motion.div 
               key={i} 
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               transition={{ delay: i * 0.1 }}
               className="flex flex-col gap-1 cursor-crosshair group"
             >
               <div className="flex items-center gap-2">
                  <div className={`w-4 h-[1px] ${item.color.replace('text-', 'bg-')}`} />
                  <span className="text-[7px] font-black text-slate-500 uppercase tracking-[0.4em]">
                    {item.label}
                  </span>
               </div>
               <Motion.div 
                 key={item.value}
                 initial={{ opacity: 0 }}
                 animate={{ opacity: 1 }}
                 className={`text-[10px] font-mono font-bold ${item.color} ml-6 tracking-widest`}
               >
                  {item.value}
               </Motion.div>
             </Motion.div>
           ))}
        </div>

        <section className="flex-1 flex flex-col items-center justify-center relative p-8">
          <Motion.div 
            animate={{ 
              scale: currentSenses?.isLooking ? 1.05 : 1,
              filter: currentSenses?.isLooking ? "brightness(1.2)" : "brightness(1)"
            }}
            transition={{ duration: 0.5 }}
            className="w-full h-full flex items-center justify-center"
          >
            <NeuralSchema 
              isLooking={currentSenses?.isLooking} 
              emotion={currentSenses?.emotion || 'neutral'} 
            />
          </Motion.div>

          <div className="absolute inset-0 pointer-events-none z-50">
             {/* Centered Popup Container */}
             <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <AnimatePresence mode="wait">
                  {isChatOpen && (
                    <Motion.div 
                      key="chat-popup"
                      initial={{ scale: 0.9, opacity: 0, y: 20 }}
                      animate={{ scale: 1, opacity: 1, y: 0 }}
                      exit={{ scale: 0.9, opacity: 0, y: 20 }}
                      className="pointer-events-auto"
                    >
                      <ChatPanel onClose={() => setIsChatOpen(false)} />
                    </Motion.div>
                  )}
                  {isLogOpen && (
                    <Motion.div 
                      key="log-popup"
                      initial={{ scale: 0.9, opacity: 0, y: 20 }}
                      animate={{ scale: 1, opacity: 1, y: 0 }}
                      exit={{ scale: 0.9, opacity: 0, y: 20 }}
                      className="pointer-events-auto"
                    >
                      <NeuralLog />
                    </Motion.div>
                  )}
                </AnimatePresence>
             </div>

             <div className="absolute top-12 right-12 pointer-events-auto">
               <AIPanel />
             </div>
             {/* Dynamic Sense Feed Thumbnail */}
             <div className="absolute bottom-32 right-12 w-40 h-24 rounded-2xl overflow-hidden border border-white/10 bg-black/60 backdrop-blur-xl pointer-events-auto group hover:border-brand-cyan/40 transition-all shadow-2xl">
                <div className="absolute inset-0 bg-brand-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="absolute top-3 left-3 flex items-center justify-between w-[calc(100%-1.5rem)] z-10">
                   <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full animate-pulse ${currentSenses?.isLooking ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'}`} />
                      <span className="text-[8px] font-black text-white/50 tracking-widest uppercase">Live_Sense_Uplink</span>
                   </div>
                   
                </div>
                <div className="w-full h-full relative">
                   <NeuralPulse 
                     color={currentSenses?.isLooking ? "#00f2ff" : "#ef4444"} 
                     speed={currentSenses?.isLooking ? 1.5 : 0.5} 
                   />
                   
                   {currentSenses?.isLooking && (
                     <Motion.div 
                       className="absolute inset-0 border-2 border-brand-cyan/10"
                       animate={{ opacity: [0.1, 0.3, 0.1], scale: [1, 1.02, 1] }}
                       transition={{ duration: 2, repeat: Infinity }}
                     />
                   )}
                </div>

                <div className="absolute bottom-2 left-3 flex gap-4">
                   <div className="flex flex-col">
                      <span className="text-[6px] text-slate-600 font-bold uppercase">Signal</span>
                      <span className="text-[8px] font-mono text-emerald-400">98.4%</span>
                   </div>
                   <div className="flex flex-col">
                      <span className="text-[6px] text-slate-600 font-bold uppercase">Sync</span>
                      <span className="text-[8px] font-mono text-brand-cyan">Stable</span>
                   </div>
                </div>
             </div>
          </div>

          <HumanSenses onSenseUpdate={handleSenseUpdate} />

          {/* Centered Trigger Dock */}
          <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex items-center gap-6 p-2 px-6 rounded-3xl bg-black/40 border border-white/10 backdrop-blur-2xl z-[100] shadow-[0_10px_40px_rgba(0,0,0,0.4)] pointer-events-auto">
            <TriggerButton 
              active={isChatOpen} 
              onClick={() => { setIsChatOpen(!isChatOpen); setIsLogOpen(false); setIsHackingOpen(false); }}
              icon={MessageSquare}
              activeColor="bg-brand-cyan/20 text-brand-cyan"
            />
            <TriggerButton 
              active={isHackingOpen} 
              onClick={() => { setIsHackingOpen(!isHackingOpen); setIsChatOpen(false); setIsLogOpen(false); }}
              icon={Shield}
              activeColor="bg-brand-purple/20 text-brand-purple"
            />
            <div className="w-[1px] h-8 bg-white/10" />
            <TriggerButton 
              active={isLogOpen} 
              onClick={() => { setIsLogOpen(!isLogOpen); setIsChatOpen(false); setIsHackingOpen(false); }}
              icon={Activity}
              activeColor="bg-brand-purple/20 text-brand-purple"
            />
          </div>
        </section>
      </main>
    </div>
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
