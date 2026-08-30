'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';

import axios from 'axios';
import GlassCard from '../ui/GlassCard';
import ProgressBar from '../ui/ProgressBar';
import { API_BASE_URL } from '../../config';
import { Play, Pause, RotateCcw, RefreshCw, Layers } from 'lucide-react';

const defaultAutomations = [
  { id: "web_search", name: "Web Search Automation", category: "INTELLIGENCE", val: 75, status: "Running", color: "bg-cyan-400", description: "Crawling real-time indices, security alerts, and threat bulletins." },
  { id: "email_draft", name: "Email Draft Generator", category: "COMMUNICATION", val: 60, status: "Running", color: "bg-cyan-400", description: "Synthesizing project reports & generating neural email drafts." },
  { id: "file_organizer", name: "File Organizer", category: "FILESYSTEM", val: 100, status: "Completed", color: "bg-emerald-400", description: "Indexed workspace artifacts and cleaned temporary system staging." },
  { id: "meeting_assistant", name: "AI Meeting Assistant", category: "PRODUCTIVITY", val: 0, status: "Idle", color: "bg-slate-700", description: "Standing by to transcribe voice streams and aggregate action items." },
  { id: "data_extractor", name: "Data Extractor", category: "ANALYTICS", val: 40, status: "Running", color: "bg-cyan-400", description: "Extracting structured entities from memory database & telemetry logs." },
  { id: "system_optimizer", name: "System Cache Optimizer", category: "SYSTEM", val: 85, status: "Running", color: "bg-purple-400", description: "Defragmenting memory pipelines and trimming runtime buffers." }
];

const ActiveAutomations = () => {
  const [automations, setAutomations] = useState(defaultAutomations);
  const [actionLoading, setActionLoading] = useState({});
  const [isSyncing, setIsSyncing] = useState(false);
  const wsRef = useRef(null);

  // Fetch automations from Python backend
  const fetchAutomations = useCallback(async () => {
    try {
      setIsSyncing(true);
      const res = await axios.get(`${API_BASE_URL}/api/automations/list`, { timeout: 3500 });
      if (res.data?.success && Array.isArray(res.data.automations) && res.data.automations.length > 0) {
        setAutomations(res.data.automations);
      }
    } catch (e) {
      // Backend fallback gracefully
    } finally {
      setIsSyncing(false);
    }
  }, []);

  useEffect(() => {
    fetchAutomations();

    // WebSocket real-time subscription
    let ws = null;
    try {
      const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws/tasks';
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event === 'INITIAL_STATE' && data.all_automations) {
            setAutomations(data.all_automations);
          } else if (data.event === 'AUTOMATION_UPDATED' && data.automation) {
            setAutomations((prev) =>
              prev.map((item) => (item.id === data.automation.id ? data.automation : item))
            );
          } else if (data.all_automations) {
            setAutomations(data.all_automations);
          }
        } catch (err) {
          // Ignore parse errors
        }
      };
    } catch (err) {
      console.debug('WS connection error in ActiveAutomations', err);
    }

    const interval = setInterval(fetchAutomations, 10000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, [fetchAutomations]);

  const handleTrigger = async (id, e) => {
    e.stopPropagation();
    try {
      setActionLoading((prev) => ({ ...prev, [id]: true }));
      setAutomations((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: 'Running', val: 10, color: 'bg-cyan-400' } : item
        )
      );
      await axios.post(`${API_BASE_URL}/api/automations/trigger`, { id });
    } catch (err) {
      console.warn('Failed to trigger automation:', err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: false }));
    }
  };

  const handlePause = async (id, e) => {
    e.stopPropagation();
    try {
      setActionLoading((prev) => ({ ...prev, [id]: true }));
      setAutomations((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, status: item.status === 'Running' ? 'Paused' : 'Running' }
            : item
        )
      );
      await axios.post(`${API_BASE_URL}/api/automations/pause`, { id });
    } catch (err) {
      console.warn('Failed to pause automation:', err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: false }));
    }
  };

  const handleReset = async (id, e) => {
    e.stopPropagation();
    try {
      setActionLoading((prev) => ({ ...prev, [id]: true }));
      setAutomations((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: 'Idle', val: 0, color: 'bg-slate-700' } : item
        )
      );
      await axios.post(`${API_BASE_URL}/api/automations/reset`, { id });
    } catch (err) {
      console.warn('Failed to reset automation:', err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: false }));
    }
  };

  return (
    <GlassCard 
      title="Active Automations" 
      className="h-[360px] lg:h-full flex flex-col min-h-0"
    >
      <div className="flex-1 flex flex-col justify-between overflow-y-auto pr-1 space-y-2.5 my-1 pt-1 min-h-0 custom-scrollbar">
        {automations.map((task) => {
          const isRunning = task.status?.toLowerCase() === 'running';
          const isCompleted = task.status?.toLowerCase() === 'completed';
          const isPaused = task.status?.toLowerCase() === 'paused';

          return (
            <div 
              key={task.id || task.name} 
              className="p-2.5 rounded-lg bg-black/40 border border-white/[0.04] hover:border-cyan-500/30 transition-all duration-200 group flex flex-col gap-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    isRunning ? 'bg-cyan-400 animate-pulse shadow-[0_0_6px_rgba(0,229,255,0.8)]' :
                    isCompleted ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' :
                    isPaused ? 'bg-amber-400' : 'bg-slate-600'
                  } shrink-0`} />
                  <span className="text-[10px] font-bold text-slate-200 truncate uppercase tracking-wider">
                    {task.name}
                  </span>
                  {task.category && (
                    <span className="text-[7px] px-1 py-0.2 bg-cyan-950/60 border border-cyan-500/20 text-cyan-400 font-mono rounded">
                      {task.category}
                    </span>
                  )}
                </div>

                {/* Quick Action Controls */}
                <div className="flex items-center gap-1 shrink-0">
                  {isRunning ? (
                    <button
                      onClick={(e) => handlePause(task.id, e)}
                      disabled={actionLoading[task.id]}
                      title="Pause Automation"
                      className="p-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 text-[8px] transition-all active:scale-95 cursor-pointer"
                    >
                      <Pause className="w-2.5 h-2.5" />
                    </button>
                  ) : (
                    <button
                      onClick={(e) => handleTrigger(task.id, e)}
                      disabled={actionLoading[task.id]}
                      title="Run Automation"
                      className="p-1 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 text-[8px] transition-all active:scale-95 flex items-center gap-1 cursor-pointer"
                    >
                      <Play className="w-2.5 h-2.5 fill-current" />
                    </button>
                  )}
                  <button
                    onClick={(e) => handleReset(task.id, e)}
                    disabled={actionLoading[task.id]}
                    title="Reset Automation"
                    className="p-1 rounded bg-white/[0.04] hover:bg-white/[0.1] text-slate-400 border border-white/[0.06] text-[8px] transition-all active:scale-95 cursor-pointer"
                  >
                    <RotateCcw className="w-2.5 h-2.5" />
                  </button>
                </div>
              </div>

              {/* Progress Bar with Live % and Status */}
              <ProgressBar 
                label="" 
                value={task.val} 
                isPurple={isRunning ? false : (isCompleted ? false : isPaused ? true : false)} 
                status={task.status} 
              />
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};

export default ActiveAutomations;
