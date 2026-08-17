import React, { useState } from 'react';
import GlassCard from '../ui/GlassCard';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle,
  Play,
  RotateCcw,
  XCircle,
  ChevronDown,
  ChevronUp,
  Cpu,
  HardDrive,
  Terminal,
  Globe,
  Folder,
  Code2,
  Search,
  Monitor,
  Database,
  Layers
} from 'lucide-react';

const LiveTaskDashboard = ({
  tasks = [],
  stats = { total: 0, running: 0, waiting: 0, completed: 0, failed: 0 },
  isConnected = false,
  onCancelTask,
  onRetryTask
}) => {
  const [activeTab, setActiveTab] = useState('ALL');
  const [expandedTaskId, setExpandedTaskId] = useState(null);

  const filteredTasks = tasks.filter((task) => {
    if (activeTab === 'RUNNING') return task.status === 'RUNNING';
    if (activeTab === 'WAITING') return task.status === 'QUEUED';
    if (activeTab === 'COMPLETED') return task.status === 'COMPLETED';
    if (activeTab === 'FAILED') return task.status === 'FAILED' || task.status === 'CANCELED';
    return true;
  });

  const getAgentIcon = (agentType) => {
    switch (agentType) {
      case 'browser':
        return <Globe size={13} className="text-cyan-400" />;
      case 'file':
        return <Folder size={13} className="text-emerald-400" />;
      case 'coding':
        return <Code2 size={13} className="text-purple-400" />;
      case 'search':
        return <Search size={13} className="text-pink-400" />;
      case 'terminal':
        return <Terminal size={13} className="text-amber-400" />;
      case 'memory':
        return <Database size={13} className="text-blue-400" />;
      default:
        return <Monitor size={13} className="text-sky-400" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            RUNNING
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
            <Clock size={9} />
            WAITING
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle size={9} />
            DONE
          </span>
        );
      case 'FAILED':
      case 'CANCELED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <XCircle size={9} />
            {status}
          </span>
        );
      default:
        return null;
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return <span className="text-[8px] font-black text-rose-400 uppercase tracking-widest">CRITICAL</span>;
      case 'HIGH':
        return <span className="text-[8px] font-bold text-amber-400 uppercase tracking-widest">HIGH</span>;
      case 'LOW':
        return <span className="text-[8px] font-medium text-slate-400 uppercase tracking-widest">LOW</span>;
      default:
        return <span className="text-[8px] font-medium text-cyan-400 uppercase tracking-widest">MED</span>;
    }
  };

  return (
    <GlassCard
      title="Live Multi-Agent Orchestrator"
      headerRight={
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className="text-[9px] font-mono text-slate-400 uppercase">
            {isConnected ? 'STREAM_LINK' : 'OFFLINE_SYNC'}
          </span>
        </div>
      }
      className="flex flex-col h-full min-h-[300px]"
    >
      {/* Stats Counter Bar */}
      <div className="grid grid-cols-5 gap-1 sm:gap-1.5 mb-2.5">
        {[
          { key: 'ALL', label: 'All Tasks', count: stats.total, color: 'text-slate-200' },
          { key: 'RUNNING', label: 'Running', count: stats.running, color: 'text-cyan-400' },
          { key: 'WAITING', label: 'Waiting', count: stats.waiting, color: 'text-amber-400' },
          { key: 'COMPLETED', label: 'Completed', count: stats.completed, color: 'text-emerald-400' },
          { key: 'FAILED', label: 'Failed', count: stats.failed, color: 'text-rose-400' }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`p-1.5 rounded-lg border text-center transition-all min-h-[38px] flex flex-col justify-center items-center ${
              activeTab === tab.key
                ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.15)]'
                : 'bg-slate-900/40 border-white/5 text-slate-400 hover:border-white/15'
            }`}
          >
            <div className={`text-[12px] font-mono font-bold leading-none ${tab.color}`}>
              {tab.count}
            </div>
            <div className="text-[7px] sm:text-[7.5px] font-semibold uppercase tracking-wider mt-0.5 truncate max-w-full">
              {tab.label}
            </div>
          </button>
        ))}
      </div>

      {/* Task Execution Feed */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0 custom-scrollbar">
        {filteredTasks.length === 0 ? (
          <div className="h-full min-h-[140px] flex flex-col items-center justify-center text-center p-4 border border-dashed border-white/10 rounded-xl">
            <Layers className="text-slate-600 mb-2 animate-bounce" size={24} />
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              No tasks in queue
            </span>
            <span className="text-[9.5px] text-slate-500 mt-1 max-w-[200px]">
              Prompt OrionAI with single or multiple commands to launch background agents.
            </span>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const isExpanded = expandedTaskId === task.id;
            return (
              <motion.div
                key={task.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-2.5 rounded-xl bg-slate-900/60 border border-white/10 hover:border-cyan-500/30 transition-all flex flex-col gap-2"
              >
                {/* Task Header */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="p-1.5 rounded-lg bg-slate-800/80 border border-white/10 shrink-0">
                      {getAgentIcon(task.agent_type)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10.5px] font-bold text-white truncate leading-snug">
                          {task.command}
                        </span>
                        {getPriorityBadge(task.priority)}
                      </div>
                      <span className="text-[8px] font-mono text-slate-400 capitalize block truncate mt-0.5">
                        Agent: {task.agent_type} • ID: {task.id}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {getStatusBadge(task.status)}
                    {task.status === 'RUNNING' && (
                      <button
                        onClick={() => onCancelTask && onCancelTask(task.id)}
                        title="Cancel Task"
                        className="p-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all"
                      >
                        <XCircle size={12} />
                      </button>
                    )}
                    {(task.status === 'FAILED' || task.status === 'CANCELED') && (
                      <button
                        onClick={() => onRetryTask && onRetryTask(task.id)}
                        title="Retry Task"
                        className="p-1 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-all"
                      >
                        <RotateCcw size={12} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Progress Bar & Current Action */}
                <div className="space-y-1">
                  <div className="flex justify-between items-center text-[8.5px] font-mono">
                    <span className="text-slate-300 truncate max-w-[70%]">
                      {task.current_action}
                    </span>
                    <span className="text-cyan-400 font-bold">{task.progress}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-white/5">
                    <motion.div
                      className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${task.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>

                {/* Telemetry Footer & Expand Logs Trigger */}
                <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[8px] font-mono text-slate-400">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-0.5">
                      <Cpu size={9} className="text-cyan-400" /> CPU: {task.cpu_usage || 0}%
                    </span>
                    <span className="flex items-center gap-0.5">
                      <HardDrive size={9} className="text-purple-400" /> RAM: {task.mem_usage || 0}%
                    </span>
                    {task.eta_seconds > 0 && task.status === 'RUNNING' && (
                      <span className="text-amber-400 font-bold">ETA: ~{task.eta_seconds}s</span>
                    )}
                  </div>

                  <button
                    onClick={() => setExpandedTaskId(isExpanded ? null : task.id)}
                    className="flex items-center gap-1 text-slate-400 hover:text-cyan-300 transition-colors uppercase font-semibold"
                  >
                    <span>Logs ({task.logs?.length || 0})</span>
                    {isExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                  </button>
                </div>

                {/* Execution Logs Accordion */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden mt-1 p-2 rounded-lg bg-black/60 border border-white/10 font-mono text-[8px] text-cyan-300 space-y-1 max-h-32 overflow-y-auto custom-scrollbar"
                    >
                      {task.logs && task.logs.length > 0 ? (
                        task.logs.map((log, idx) => (
                          <div key={idx} className="leading-tight break-all">
                            {log}
                          </div>
                        ))
                      ) : (
                        <div className="text-slate-500">No execution logs recorded yet.</div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })
        )}
      </div>
    </GlassCard>
  );
};

export default LiveTaskDashboard;
