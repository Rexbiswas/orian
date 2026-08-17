import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, Eye, Shield, Database, Code2, Sparkles, CheckCircle2 } from 'lucide-react';
import { speak, unlockAudio } from '../../utils/voice';
import { playSuccessChime, playMicActivate } from '../../utils/sound';
import { useVoice } from '../../context/VoiceContext';

export const BRAIN_AGENTS = [
  {
    id: 'cortex',
    name: 'CORTEX AI',
    role: 'Reasoning & Intelligence',
    icon: Brain,
    color: '#00FF66',
    textColor: 'text-[#00FF66]',
    borderColor: 'border-[#00FF66]/40',
    glowColor: 'rgba(0, 255, 102, 0.4)',
    status: 'ONLINE'
  },
  {
    id: 'titan',
    name: 'TITAN AI',
    role: 'Action & Execution',
    icon: Zap,
    color: '#00E5FF',
    textColor: 'text-[#00E5FF]',
    borderColor: 'border-[#00E5FF]/40',
    glowColor: 'rgba(0, 229, 255, 0.4)',
    status: 'ONLINE'
  },
  {
    id: 'spectra',
    name: 'SPECTRA AI',
    role: 'Perception & Vision',
    icon: Eye,
    color: '#FF007F',
    textColor: 'text-[#FF007F]',
    borderColor: 'border-[#FF007F]/40',
    glowColor: 'rgba(255, 0, 127, 0.4)',
    status: 'ONLINE'
  },
  {
    id: 'guardian',
    name: 'GUARDIAN AI',
    role: 'Security & Defense',
    icon: Shield,
    color: '#00FFCC',
    textColor: 'text-[#00FFCC]',
    borderColor: 'border-[#00FFCC]/40',
    glowColor: 'rgba(0, 255, 204, 0.4)',
    status: 'ONLINE'
  },
  {
    id: 'nexus',
    name: 'NEXUS AI',
    role: 'Memory & State Timeline',
    icon: Database,
    color: '#A855F7',
    textColor: 'text-[#A855F7]',
    borderColor: 'border-[#A855F7]/40',
    glowColor: 'rgba(168, 85, 247, 0.4)',
    status: 'ONLINE'
  },
  {
    id: 'oracle',
    name: 'ORACLE AI',
    role: 'Self-Programming & Code',
    icon: Code2,
    color: '#F59E0B',
    textColor: 'text-[#F59E0B]',
    borderColor: 'border-[#F59E0B]/40',
    glowColor: 'rgba(245, 158, 11, 0.4)',
    status: 'ONLINE'
  }
];

const AnimatedBrainCells = ({ onAgentOnline }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCellId, setActiveCellId] = useState('titan');
  const [activeAnnouncement, setActiveAnnouncement] = useState('');
  const { setSpeakingState } = useVoice();
  const menuRef = useRef(null);

  // Announce & speak agent online greeting
  const triggerAgentOnline = useCallback(async (agent) => {
    const greeting = `${agent.name.toLowerCase()} agent is online`;
    setActiveAnnouncement(greeting);
    setActiveCellId(agent.id);

    unlockAudio();
    playSuccessChime();

    try {
      await speak(greeting, setSpeakingState);
    } catch (e) {
      console.warn("Agent online TTS greeting fault:", e);
    }

    if (onAgentOnline) {
      onAgentOnline(agent, greeting);
    }

    // Broadcast globally to other components
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('orian-agent-online', {
        detail: { agent, agentName: agent.name, message: greeting }
      }));
    }

    setTimeout(() => {
      setActiveAnnouncement('');
    }, 4500);
  }, [setSpeakingState, onAgentOnline]);

  // Listen to remote or internal agent online events
  useEffect(() => {
    const handleRemoteOnline = (e) => {
      const { agentName } = e.detail || {};
      if (agentName) {
        const found = BRAIN_AGENTS.find(a => a.name.toLowerCase().includes(agentName.toLowerCase()) || a.id === agentName.toLowerCase());
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
      {/* Animated Glowing Brain Core Button */}
      <button
        onClick={() => {
          unlockAudio();
          playMicActivate();
          setIsOpen(prev => !prev);
          // Default click triggers TITAN AI online greeting if closed
          if (!isOpen) {
            const titanAgent = BRAIN_AGENTS.find(a => a.id === 'titan') || BRAIN_AGENTS[1];
            triggerAgentOnline(titanAgent);
          }
        }}
        title="Orian Neural Brain & 6 Agent Cells"
        aria-label="Orian Neural Brain"
        className="relative group w-9 h-9 rounded-xl bg-gradient-to-br from-[#061536] to-[#020512] border border-cyan-400/40 hover:border-cyan-400 flex items-center justify-center cursor-pointer transition-all duration-300 shadow-[0_0_15px_rgba(0,229,255,0.25)] hover:shadow-[0_0_25px_rgba(0,229,255,0.5)] active:scale-95"
      >
        {/* Pulsing Synapse Rings */}
        <span className="absolute -inset-1 rounded-xl border border-cyan-400/20 animate-ping pointer-events-none opacity-40" />
        <span className="absolute -inset-0.5 rounded-xl border border-purple-500/30 animate-pulse pointer-events-none" />

        {/* Orbiting Brain Synaptic Cell Particles */}
        <div className="absolute inset-0 pointer-events-none overflow-visible">
          {[0, 60, 120, 180, 240, 300].map((deg, idx) => (
            <motion.span
              key={deg}
              animate={{
                rotate: [deg, deg + 360],
                scale: [0.8, 1.2, 0.8],
                opacity: [0.4, 0.9, 0.4]
              }}
              transition={{
                duration: 8 + idx,
                repeat: Infinity,
                ease: "linear"
              }}
              className="absolute top-1/2 left-1/2 w-1.5 h-1.5 -ml-[3px] -mt-[3px] rounded-full"
              style={{
                backgroundColor: BRAIN_AGENTS[idx]?.color || '#00E5FF',
                boxShadow: `0 0 6px ${BRAIN_AGENTS[idx]?.color || '#00E5FF'}`,
                transformOrigin: '16px 16px'
              }}
            />
          ))}
        </div>

        {/* Central Animated Brain Icon */}
        <Brain
          size={18}
          className="text-cyan-300 group-hover:text-white transition-colors animate-pulse drop-shadow-[0_0_8px_rgba(0,229,255,0.8)] z-10"
        />
      </button>

      {/* Floating 6 Brain Cells Popover */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ type: 'spring', damping: 22, stiffness: 260 }}
            className="absolute top-12 left-0 w-72 sm:w-80 bg-[#020617]/95 border border-cyan-500/30 rounded-2xl p-3.5 backdrop-blur-2xl shadow-[0_15px_40px_rgba(0,0,0,0.9),0_0_30px_rgba(0,229,255,0.18)] z-50 flex flex-col gap-2.5 font-mono"
          >
            {/* Popover Header */}
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <div className="flex items-center gap-1.5">
                <Brain size={14} className="text-cyan-400" />
                <span className="text-[10px] font-black uppercase tracking-widest text-cyan-300">
                  Neural Brain Cells (6 Agents)
                </span>
              </div>
              <span className="text-[8px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                ALL SYNCED
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
                      <span className="text-[7px] text-slate-400 truncate max-w-[70%]">
                        {agent.role}
                      </span>
                      <span
                        className="text-[7.5px] font-bold uppercase tracking-wider flex items-center gap-0.5"
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
