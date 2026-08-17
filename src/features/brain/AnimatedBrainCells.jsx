import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, Eye, Shield, Database, Sparkles } from 'lucide-react';
import { speak, unlockAudio } from '../../utils/voice';
import { playSuccessChime, playMicActivate } from '../../utils/sound';
import { useVoice } from '../../context/VoiceContext';

export const BRAIN_AGENTS = [
  {
    id: 'cortex',
    name: 'CORTEX AI',
    role: 'Reasoning',
    greeting: 'cortex ai reasoning agent is online',
    icon: Brain,
    color: '#00FF66',
    textColor: 'text-[#00FF66]',
    borderColor: 'border-[#00FF66]/40',
    glowColor: 'rgba(0, 255, 102, 0.4)',
    status: 'ONLINE',
    offset: { x: -6, y: -5 }
  },
  {
    id: 'titan',
    name: 'TITAN AI',
    role: 'Orchestrator',
    greeting: 'titan ai orchestrator agent is online',
    icon: Zap,
    color: '#00E5FF',
    textColor: 'text-[#00E5FF]',
    borderColor: 'border-[#00E5FF]/40',
    glowColor: 'rgba(0, 229, 255, 0.4)',
    status: 'ONLINE',
    offset: { x: 6, y: -5 }
  },
  {
    id: 'spectra',
    name: 'SPECTRA AI',
    role: 'Sensory',
    greeting: 'spectra ai sensory agent is online',
    icon: Eye,
    color: '#FF007F',
    textColor: 'text-[#FF007F]',
    borderColor: 'border-[#FF007F]/40',
    glowColor: 'rgba(255, 0, 127, 0.4)',
    status: 'ONLINE',
    offset: { x: -9, y: 1 }
  },
  {
    id: 'guardian',
    name: 'GUARDIAN AI',
    role: 'Defense',
    greeting: 'guardian ai defense agent is online',
    icon: Shield,
    color: '#00FFCC',
    textColor: 'text-[#00FFCC]',
    borderColor: 'border-[#00FFCC]/40',
    glowColor: 'rgba(0, 255, 204, 0.4)',
    status: 'ONLINE',
    offset: { x: 9, y: 1 }
  },
  {
    id: 'database',
    name: 'Database Cluster',
    role: 'Memory & State',
    greeting: 'database cluster is online',
    icon: Database,
    color: '#A855F7',
    textColor: 'text-[#A855F7]',
    borderColor: 'border-[#A855F7]/40',
    glowColor: 'rgba(168, 85, 247, 0.4)',
    status: 'ONLINE',
    offset: { x: -5, y: 7 }
  },
  {
    id: 'shield',
    name: 'Security Shield',
    role: 'Protection & Firewall',
    greeting: 'security shield is online',
    icon: Shield,
    color: '#F59E0B',
    textColor: 'text-[#F59E0B]',
    borderColor: 'border-[#F59E0B]/40',
    glowColor: 'rgba(245, 158, 11, 0.4)',
    status: 'ONLINE',
    offset: { x: 5, y: 7 }
  }
];

const AnimatedBrainCells = ({ onAgentOnline }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCellId, setActiveCellId] = useState('titan');
  const { setSpeakingState } = useVoice();
  const menuRef = useRef(null);

  // Announce & speak agent online greeting
  const triggerAgentOnline = useCallback(async (agent) => {
    const greetingMsg = agent.greeting || `${agent.name.toLowerCase()} agent is online`;
    setActiveCellId(agent.id);

    unlockAudio();
    playSuccessChime();

    try {
      await speak(greetingMsg, setSpeakingState);
    } catch (e) {
      console.warn("Agent online TTS greeting fault:", e);
    }

    if (onAgentOnline) {
      onAgentOnline(agent, greetingMsg);
    }

    // Broadcast globally to other components
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('orian-agent-online', {
        detail: { agent, agentName: agent.name, message: greetingMsg }
      }));
    }
  }, [setSpeakingState, onAgentOnline]);

  // Listen to remote or internal agent online events
  useEffect(() => {
    const handleRemoteOnline = (e) => {
      const { agentName } = e.detail || {};
      if (agentName) {
        const found = BRAIN_AGENTS.find(a => 
          a.name.toLowerCase().includes(agentName.toLowerCase()) || 
          a.id === agentName.toLowerCase() ||
          a.role.toLowerCase().includes(agentName.toLowerCase())
        );
        if (found) {
          triggerAgentOnline(found);
        }
      }
    };

    window.addEventListener('trigger-agent-online', handleRemoteOnline);
    return () => window.removeEventListener('trigger-agent-online', handleRemoteOnline);
  }, [triggerAgentOnline]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('pointerdown', handleClickOutside);
    }
    return () => document.removeEventListener('pointerdown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative inline-flex items-center" ref={menuRef}>
      {/* Brain Container with 6 Animated Synaptic Cells Inside */}
      <button
        onClick={() => {
          unlockAudio();
          playMicActivate();
          setIsOpen(prev => !prev);
          if (!isOpen) {
            const titanAgent = BRAIN_AGENTS.find(a => a.id === 'titan') || BRAIN_AGENTS[1];
            triggerAgentOnline(titanAgent);
          }
        }}
        title="Orian Neural Brain (6 Animated Brain Cells)"
        aria-label="Orian Neural Brain"
        className="relative group w-11 h-11 rounded-xl bg-gradient-to-b from-[#05112c] via-[#02091c] to-[#010410] border border-cyan-500/40 hover:border-cyan-400 flex items-center justify-center cursor-pointer transition-all duration-300 shadow-[0_0_16px_rgba(0,102,255,0.3)] hover:shadow-[0_0_24px_rgba(0,229,255,0.5)] active:scale-95 overflow-hidden"
      >
        {/* Soft Background Radial Glow */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,229,255,0.15),transparent_70%)] pointer-events-none" />

        {/* Central Brain Icon */}
        <Brain
          size={24}
          className="text-cyan-400/90 group-hover:text-cyan-200 transition-colors z-10 drop-shadow-[0_0_6px_rgba(0,229,255,0.6)]"
        />

        {/* 6 Animated Brain Cells Moving Inside The Brain */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center overflow-hidden z-20">
          {BRAIN_AGENTS.map((agent, i) => (
            <motion.span
              key={agent.id}
              initial={{ x: agent.offset.x, y: agent.offset.y }}
              animate={{
                x: [
                  agent.offset.x,
                  agent.offset.x + (i % 2 === 0 ? 2.5 : -2.5),
                  agent.offset.x - (i % 2 === 0 ? 2 : -2),
                  agent.offset.x
                ],
                y: [
                  agent.offset.y,
                  agent.offset.y + (i % 3 === 0 ? 2.5 : -2.5),
                  agent.offset.y - (i % 3 === 0 ? 2 : -2),
                  agent.offset.y
                ],
                scale: [1, 1.35, 0.9, 1],
                opacity: [0.85, 1, 0.75, 0.85]
              }}
              transition={{
                duration: 2.8 + (i * 0.4),
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute w-1.5 h-1.5 rounded-full"
              style={{
                backgroundColor: agent.color,
                boxShadow: `0 0 7px ${agent.color}, 0 0 12px ${agent.color}80`
              }}
            />
          ))}
        </div>
      </button>

      {/* Floating 6 Brain Cells Popover */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 8 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute top-13 left-0 w-72 sm:w-84 bg-[#020617]/95 border border-cyan-500/35 rounded-2xl p-3.5 backdrop-blur-2xl shadow-[0_15px_40px_rgba(0,0,0,0.9),0_0_30px_rgba(0,229,255,0.2)] z-50 flex flex-col gap-2.5 font-mono"
          >
            {/* Popover Header */}
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <div className="flex items-center gap-1.5">
                <Brain size={15} className="text-cyan-400" />
                <span className="text-[10px] font-black uppercase tracking-widest text-cyan-300">
                  Neural Brain Cells (6 Agents)
                </span>
              </div>
              <span className="text-[8px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                ACTIVE & SYNCED
              </span>
            </div>

            {/* 6 Brain Agent Cells Grid */}
            <div className="grid grid-cols-2 gap-2">
              {BRAIN_AGENTS.map((agent) => {
                const Icon = agent.icon;
                const isActive = activeCellId === agent.id;

                return (
                  <button
                    key={agent.id}
                    onClick={() => triggerAgentOnline(agent)}
                    title={`Activate ${agent.name}`}
                    className={`flex flex-col p-2.5 rounded-xl border text-left transition-all duration-200 cursor-pointer active:scale-95 relative overflow-hidden group ${
                      isActive
                        ? `${agent.borderColor} bg-white/10 shadow-[0_0_15px_${agent.glowColor}]`
                        : 'border-white/10 bg-slate-900/60 hover:border-white/25 hover:bg-slate-900/90'
                    }`}
                  >
                    {/* Top Row: Icon + Name */}
                    <div className="flex items-center gap-1.5 mb-1">
                      <div
                        className="w-5 h-5 rounded-lg flex items-center justify-center shrink-0 border"
                        style={{
                          backgroundColor: `${agent.color}15`,
                          borderColor: `${agent.color}40`
                        }}
                      >
                        <Icon size={11} style={{ color: agent.color }} />
                      </div>
                      <span className="text-[9px] font-black tracking-wider text-slate-200 group-hover:text-white truncate">
                        {agent.name}
                      </span>
                    </div>

                    {/* Role & Status */}
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-[7.5px] text-slate-400 truncate max-w-[70%] font-medium">
                        {agent.role}
                      </span>
                      <span
                        className="text-[7.5px] font-bold uppercase tracking-wider flex items-center gap-1"
                        style={{ color: agent.color }}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full animate-pulse"
                          style={{ backgroundColor: agent.color }}
                        />
                        ON
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Popover Footer Info */}
            <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[8px] text-slate-400">
              <span className="flex items-center gap-1">
                <Sparkles size={10} className="text-cyan-400" />
                Tap any cell to announce & greet online
              </span>
              <span className="text-cyan-400 font-bold">OS v2.0.1</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AnimatedBrainCells;
