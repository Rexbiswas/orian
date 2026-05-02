import React, { useState, useEffect, useCallback } from 'react';
import Navbar from '../components/Navbar';
import NeuralSchema from '../components/NeuralSchema';
import AIPanel from '../components/AIPanel';
import ChatPanel from '../components/ChatPanel';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import NeuralLog from '../components/NeuralLog';
import HumanSenses from '../components/HumanSenses/HumanSenses';
import { LogProvider, useLogs } from '../context/LogContext';
import { MessageSquare, Activity } from 'lucide-react';
import { speak } from '../utils/voice';

const TriggerButton = ({ active, onClick, icon: Icon, color }) => (
  <Motion.button
    whileHover={{ scale: 1.1 }}
    whileTap={{ scale: 0.9 }}
    onClick={onClick}
    className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all overflow-hidden group pointer-events-auto border ${
      active 
      ? `bg-${color}/20 border-${color} text-${color} shadow-[0_0_20px_rgba(0,242,255,0.3)]` 
      : 'bg-slate-900/50 border-white/10 text-slate-400'
    }`}
  >
    <Icon size={24} />
  </Motion.button>
);

const FirstPageLayoutContent = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { isLogOpen, setIsLogOpen, addLog } = useLogs();
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
      addLog('VOICE_ENGINE_ACTIVATED', 'SYS', 'SUCCESS');
      await speak("Hello master, I am Orian. My human senses are now online.");
      addLog('HUMAN_SENSES_SYNC_COMPLETE', 'SYS', 'INFO');
    };
    triggerGreeting();
  }, [hasGreeted, addLog]);

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
        <section className="flex-1 flex flex-col items-center justify-center relative p-8">
          <Motion.div 
            animate={{ 
              scale: currentSenses?.isLooking ? 1.05 : 1,
              filter: currentSenses?.isLooking ? "brightness(1.2)" : "brightness(1)"
            }}
            transition={{ duration: 0.5 }}
            className="w-full h-full flex items-center justify-center"
          >
            <NeuralSchema isLooking={currentSenses?.isLooking} />
          </Motion.div>

          <div className="absolute top-12 left-12 flex flex-col gap-6 pointer-events-auto">
             {[
               { label: "PROTOCOL", value: "GENESIS_OS", color: "text-brand-cyan" },
               { label: "EMOTION_LINK", value: currentSenses?.emotion?.toUpperCase() || "SYNCING...", color: "text-yellow-400" },
               { label: "EYE_CONTACT", value: currentSenses?.isLooking ? "ESTABLISHED" : "SEARCHING", color: currentSenses?.isLooking ? "text-green-400" : "text-red-400" }
             ].map((item, i) => (
               <Motion.div key={i} className="flex flex-col gap-1 cursor-crosshair group">
                 <div className="flex items-center gap-2">
                    <div className={`w-4 h-[1px] ${item.color.replace('text-', 'bg-')}`} />
                    <span className="text-[7px] font-black text-slate-500 uppercase tracking-[0.4em]">
                      {item.label}
                    </span>
                 </div>
                 <div className={`text-[10px] font-mono font-bold ${item.color} ml-6 tracking-widest`}>
                    {item.value}
                 </div>
               </Motion.div>
             ))}
          </div>

          <div className="absolute inset-0 pointer-events-none z-50">
             <div className="absolute bottom-12 left-12 pointer-events-auto">
                <AnimatePresence>
                  {isChatOpen && (
                    <Motion.div 
                      initial={{ y: 100, opacity: 0, scale: 0.9 }}
                      animate={{ y: 0, opacity: 1, scale: 1 }}
                      exit={{ y: 100, opacity: 0, scale: 0.9 }}
                    >
                      <ChatPanel onClose={() => setIsChatOpen(false)} />
                    </Motion.div>
                  )}
                </AnimatePresence>
             </div>
             <div className="absolute top-48 left-12 pointer-events-auto">
                <NeuralLog />
             </div>
             <div className="absolute top-12 right-12 pointer-events-auto">
               <AIPanel />
             </div>
          </div>

          <HumanSenses onSenseUpdate={handleSenseUpdate} />

          <div className="absolute bottom-12 left-12 flex items-center gap-4 z-[60]">
            <TriggerButton 
              active={isChatOpen} 
              onClick={() => { setIsChatOpen(!isChatOpen); setIsLogOpen(false); }}
              icon={MessageSquare}
              color="brand-cyan"
            />
            <TriggerButton 
              active={isLogOpen} 
              onClick={() => { setIsLogOpen(!isLogOpen); setIsChatOpen(false); }}
              icon={Activity}
              color="brand-purple"
            />
          </div>
        </section>
      </main>
    </div>
  );
};

const FirstPageLayout = () => (
  <LogProvider>
    <FirstPageLayoutContent />
  </LogProvider>
);

export default FirstPageLayout;
