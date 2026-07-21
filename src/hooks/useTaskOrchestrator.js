import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { speak } from '../utils/voice';

export function useTaskOrchestrator() {

  const [tasks, setTasks] = useState([]);
  const [toasts, setToasts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState({
    "CORTEX AI": "AUTONOMOUS",
    "TITAN AI": "STANDBY",
    "SPECTRA AI": "ANALYZING",
    "GUARDIAN AI": "PROTECTING"
  });
  const wsRef = useRef(null);

  const addToast = useCallback((title, message, type = 'info') => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;
    setToasts((prev) => [
      { id, title, message, type, timestamp: new Date().toLocaleTimeString() },
      ...prev.slice(0, 4) // keep max 5 toasts
    ]);
    // Auto-remove after 4.5s
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Fetch task list via REST
  const fetchTasks = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/tasks/list`);
      if (res.data && res.data.tasks) {
        setTasks(res.data.tasks);
      }
    } catch (e) {
      console.warn('[TaskOrchestrator] REST sync failed:', e.message);
    }
  }, []);

  // WebSocket connection & streaming
  useEffect(() => {
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws/tasks';
    let socket = null;

    const connectWS = () => {
      try {
        socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          setIsConnected(true);
          console.log('[TaskOrchestrator] Real-Time WebSocket link established.');
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event === 'INITIAL_STATE' || data.all_tasks) {
              setTasks(data.all_tasks || []);
            } else if (data.event === 'TASK_UPDATED' && data.task) {
              setTasks((prev) =>
                prev.map((t) => (t.id === data.task.id ? data.task : t))
              );

              if (data.task.status === 'COMPLETED' && data.task.progress === 100) {
                addToast('Task Completed', `${data.task.command} finished.`, 'success');
                // Real-time Jarvis voice cue on step completion
                speak(`${data.task.command} completed.`);
              } else if (data.task.status === 'FAILED') {
                addToast('Task Error', `${data.task.command} failed: ${data.task.error || 'Unknown error'}`, 'error');
                speak(`Attention: ${data.task.command} encountered an error.`);
              }
            } else if (data.event === 'TASKS_ADDED' && data.tasks) {
              setTasks((prev) => [...prev, ...data.tasks]);
              addToast('Multi-Task Dispatched', `${data.tasks.length} parallel actions queued.`, 'info');
            } else if (data.event === 'AGENT_STATUS_UPDATED' && data.agent) {
              setAgentStatuses((prev) => ({
                ...prev,
                [data.agent]: data.status
              }));
            }
          } catch (err) {
            console.error('[TaskOrchestrator] WS Parse Error:', err);
          }
        };


        socket.onclose = () => {
          setIsConnected(false);
          // Reconnect after 3s
          setTimeout(connectWS, 3000);
        };

        socket.onerror = () => {
          setIsConnected(false);
          socket?.close();
        };
      } catch (err) {
        console.error('[TaskOrchestrator] WS Connection Fault:', err);
      }
    };

    connectWS();
    fetchTasks();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchTasks, addToast]);

  const dispatchPrompt = useCallback(async (prompt) => {
    if (!prompt || !prompt.trim()) return;
    try {
      const res = await axios.post(`${API_BASE_URL}/api/tasks/dispatch`, { prompt });
      if (res.data && res.data.tasks) {
        setTasks(res.data.all_tasks || []);
        addToast('Prompt Dispatched', `Queued ${res.data.count} parallel tasks.`, 'info');
      }
      return res.data;
    } catch (e) {
      addToast('Dispatch Error', e.message, 'error');
    }
  }, [addToast]);

  const cancelTask = useCallback(async (taskId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/tasks/cancel`, { task_id: taskId });
      addToast('Task Canceled', `Task ${taskId} stopped.`, 'warning');
      fetchTasks();
    } catch (e) {
      console.error(e);
    }
  }, [addToast, fetchTasks]);

  const retryTask = useCallback(async (taskId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/tasks/retry`, { task_id: taskId });
      addToast('Task Requeued', `Retrying task ${taskId}...`, 'info');
      fetchTasks();
    } catch (e) {
      console.error(e);
    }
  }, [addToast, fetchTasks]);

  // Compute stats
  const stats = {
    total: tasks.length,
    running: tasks.filter((t) => t.status === 'RUNNING').length,
    waiting: tasks.filter((t) => t.status === 'QUEUED').length,
    completed: tasks.filter((t) => t.status === 'COMPLETED').length,
    failed: tasks.filter((t) => t.status === 'FAILED' || t.status === 'CANCELED').length
  };

  return {
    tasks,
    toasts,
    stats,
    agentStatuses,
    isConnected,
    dispatchPrompt,
    cancelTask,
    retryTask,
    removeToast,
    fetchTasks
  };
}
