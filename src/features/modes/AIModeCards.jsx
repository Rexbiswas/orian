import React from 'react';
import { useTaskOrchestrator } from '../../hooks/useTaskOrchestrator';
import { useVoice } from '../../context/VoiceContext';
import { Shield, Brain, Zap, Eye } from 'lucide-react';

export const AGENT_FEATURES = [
  { 
    id: "cortex",
    name: "CORTEX AI", 
    icon: Brain,
    role: "Brain & Intelligence",
    defaultStatus: "AUTONOMOUS", 
    color: "text-[#00FF66] shadow-[0_0_12px_rgba(0,255,102,0.2)]",
    borderColor: "border-[#00FF66]/30 hover:border-[#00FF66]/70",
    indicatorColor: "bg-[#00FF66]",
    badgeBg: "bg-[#00FF66]/10 text-[#00FF66] border-[#00FF66]/30",
  },
  { 
    id: "titan",
    name: "TITAN AI", 
    icon: Zap,
    role: "Action & System Control",
    defaultStatus: "STANDBY", 
    color: "text-[#00E5FF] shadow-[0_0_12px_rgba(0,229,255,0.2)]",
    borderColor: "border-[#00E5FF]/30 hover:border-[#00E5FF]/70",
    indicatorColor: "bg-[#00E5FF]",
    badgeBg: "bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/30",
  },
  { 
    id: "spectra",
    name: "SPECTRA AI", 
    icon: Eye,
    role: "Perception & Communication",
    defaultStatus: "ANALYZING", 
    color: "text-[#FF007F] shadow-[0_0_12px_rgba(255,0,127,0.2)]",
    borderColor: "border-[#FF007F]/30 hover:border-[#FF007F]/70",
    indicatorColor: "bg-[#FF007F]",
    badgeBg: "bg-[#FF007F]/10 text-[#FF007F] border-[#FF007F]/30",
  },
  { 
    id: "guardian",
    name: "GUARDIAN AI", 
    icon: Shield,
    role: "Security & Development",
    defaultStatus: "PROTECTING", 
    color: "text-[#00FFCC] shadow-[0_0_12px_rgba(0,255,204,0.2)]",
    borderColor: "border-[#00FFCC]/30 hover:border-[#00FFCC]/70",
    indicatorColor: "bg-[#00FFCC]",
    badgeBg: "bg-[#00FFCC]/10 text-[#00FFCC] border-[#00FFCC]/30",
  }
];

const AIModeCards = () => {
  const { stats, agentStatuses } = useTaskOrchestrator();
  const { isListening, isSpeaking } = useVoice();

  const getDynamicStatus = (agent) => {
    // 1. WebSocket remote status broadcast override
    const remoteStatus = agentStatuses?.[agent.name] || agentStatuses?.[agent.id];
    if (remoteStatus && remoteStatus !== 'IDLE') {
      return remoteStatus;
    }
    // 2. Real-time active state overrides
    if (agent.id === 'cortex') {
      return (stats?.waiting > 0 || stats?.running > 0) ? "REASONING" : "AUTONOMOUS";
    }
    if (agent.id === 'titan') {
      return stats?.running > 0 ? "EXECUTING" : "STANDBY";
    }
    if (agent.id === 'spectra') {
      return isSpeaking ? "SPEAKING" : isListening ? "LISTENING" : "ANALYZING";
    }
    return agent.defaultStatus;
  };

  return (
    <div className="w-full grid grid-cols-4 gap-2.5 border-t border-purple-500/10 pt-4">
      {AGENT_FEATURES.map((agent) => {
        const status = getDynamicStatus(agent);
        const isBusy = (agent.id === 'titan' && stats?.running > 0) || (agent.id === 'spectra' && (isSpeaking || isListening));
        const Icon = agent.icon;

        return (
          <div 
            key={agent.id} 
            className={`border rounded-[6px] px-2 py-2.5 flex flex-col items-center justify-center bg-[#050A18]/60 backdrop-blur-md transition-all duration-300 select-none relative group ${agent.borderColor}`}
          >
            <div className="flex items-center gap-1 mb-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${agent.indicatorColor} ${isBusy ? 'animate-ping' : 'animate-pulse'}`} />
              <Icon size={11} className={`${agent.color} shrink-0`} />
              <span className="text-[6.5px] font-bold uppercase tracking-wider text-slate-300 leading-none group-hover:text-white transition-colors">
                {agent.name}
              </span>
            </div>
            <span className={`text-[9px] font-black tracking-widest leading-none font-sans ${agent.color} ${isBusy ? 'animate-pulse' : ''}`}>
              {status}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default AIModeCards;
