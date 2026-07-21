import React, { useState } from 'react';
import { useTaskOrchestrator } from '../hooks/useTaskOrchestrator';
import { useVoice } from '../context/VoiceContext';
import { Shield, Brain, Zap, Eye, X, CheckCircle, Activity, Sparkles } from 'lucide-react';

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
    features: [
      "Memory System (Short/Long-Term)",
      "Neural Reasoning Engine",
      "Multi-Step Goal Planning",
      "Autonomous Decision Making",
      "Continuous Self-Learning",
      "Knowledge Base Management",
      "Context & Environment Awareness"
    ]
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
    features: [
      "Autonomous Multi-Task Actions",
      "Device & Hardware Control",
      "File System Management",
      "Browser Automation Engine",
      "OS Application Control",
      "REST & GraphQL API Execution",
      "Robotics & Humanoid Telemetry"
    ]
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
    features: [
      "Computer Vision Stream",
      "Real-Time Camera Processing",
      "Facial Recognition Engine",
      "YOLO Object Detection",
      "Optical Character Recognition (OCR)",
      "Speech-to-Text VAD (STT)",
      "Neural Voice Synthesis (TTS)",
      "Facial Emotion Detection",
      "Multilingual Translation"
    ]
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
    features: [
      "Cybersecurity Defense Shield",
      "Permission & Access Control",
      "Biometric Authentication",
      "Anomaly & Threat Detection",
      "AI Code Generation",
      "Automated Code Debugging",
      "Cognitive DB Management",
      "DevOps Automation",
      "Real-Time System Monitoring",
      "Autonomous System Self-Repair"
    ]
  }
];

const AIModeCards = () => {
  const { stats, agentStatuses } = useTaskOrchestrator();
  const { isListening, isSpeaking } = useVoice();
  const [selectedAgent, setSelectedAgent] = useState(null);

  const getDynamicStatus = (agent) => {
    // 1. WebSocket remote status broadcast override
    if (agentStatuses && agentStatuses[agent.name] && agentStatuses[agent.name] !== 'IDLE') {
      return agentStatuses[agent.name];
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
    <>
      {/* 4 Agent Status Cards */}
      <div className="w-full grid grid-cols-4 gap-2.5 border-t border-purple-500/10 pt-4">
        {AGENT_FEATURES.map((agent) => {
          const status = getDynamicStatus(agent);
          const isBusy = (agent.id === 'titan' && stats?.running > 0) || (agent.id === 'spectra' && (isSpeaking || isListening));
          const Icon = agent.icon;

          return (
            <div 
              key={agent.id} 
              onClick={() => setSelectedAgent(agent)}
              title={`Click to view ${agent.name} features`}
              className={`border rounded-[6px] px-2 py-2.5 flex flex-col items-center justify-center bg-[#050A18]/60 backdrop-blur-md transition-all duration-300 transform hover:scale-[1.04] hover:shadow-lg cursor-pointer select-none relative group ${agent.borderColor}`}
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

      {/* Sci-Fi HUD Feature Details Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fadeIn">
          <div className={`w-full max-w-lg bg-[#050A18]/95 border ${selectedAgent.borderColor} rounded-xl p-6 shadow-2xl relative flex flex-col gap-4 font-sans text-slate-100 overflow-hidden`}>
            
            {/* Background Sci-Fi Glow */}
            <div className={`absolute -top-24 -right-24 w-48 h-48 rounded-full ${selectedAgent.indicatorColor} opacity-10 blur-3xl pointer-events-none`} />

            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${selectedAgent.borderColor} bg-black/40 ${selectedAgent.color}`}>
                  {React.createElement(selectedAgent.icon, { size: 20 })}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-black tracking-wider text-white uppercase">{selectedAgent.name}</h3>
                    <span className={`text-[8px] font-bold px-2 py-0.5 rounded border ${selectedAgent.badgeBg}`}>
                      {getDynamicStatus(selectedAgent)}
                    </span>
                  </div>
                  <p className="text-[11px] font-medium text-slate-400">{selectedAgent.role}</p>
                </div>
              </div>

              <button 
                onClick={() => setSelectedAgent(null)}
                className="w-8 h-8 rounded-lg border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all"
              >
                <X size={16} />
              </button>
            </div>

            {/* Feature List */}
            <div className="flex flex-col gap-2.5 my-1">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-1.5">
                <Sparkles size={12} className="text-cyan-400" />
                Active Capabilities & Features ({selectedAgent.features.length})
              </span>

              <div className="grid grid-cols-1 gap-2 max-h-[260px] overflow-y-auto pr-1">
                {selectedAgent.features.map((feature, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.08] hover:border-white/20 transition-all group"
                  >
                    <CheckCircle size={14} className={`${selectedAgent.color} shrink-0 group-hover:scale-110 transition-transform`} />
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-white transition-colors">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-white/10 pt-4 text-[10px] font-mono text-slate-400">
              <span className="flex items-center gap-1">
                <Activity size={12} className="text-emerald-400" /> SYSTEM NODE: ONLINE
              </span>
              <button
                onClick={() => setSelectedAgent(null)}
                className={`px-4 py-1.5 rounded-lg border font-bold uppercase tracking-wider text-[10px] ${selectedAgent.badgeBg} hover:opacity-90 transition-all`}
              >
                Close HUD
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AIModeCards;
