'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

import { getSyncedDate } from '../utils/timeSync';

const LogContext = createContext();

export const useLogs = () => {
  const context = useContext(LogContext);
  if (!context) {
    throw new Error('useLogs must be used within a LogProvider');
  }
  return context;
};

export const LogProvider = ({ children }) => {
  const [isLogOpen, setIsLogOpen] = useState(false);
  const [logs, setLogs] = useState([
    { id: '1', type: 'SYS', message: 'Neural Interface Initialized', status: 'SUCCESS', timestamp: getSyncedDate().toLocaleTimeString() },
    { id: '2', type: 'NET', message: 'Quantum Uplink Established', status: 'INFO', timestamp: getSyncedDate().toLocaleTimeString() },
    { id: '3', type: 'MEM', message: 'Core Cache Optimized', status: 'INFO', timestamp: getSyncedDate().toLocaleTimeString() },
  ]);

  const addLog = useCallback((message, type = 'EXEC', status = 'INFO') => {
    const newLog = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      status,
      timestamp: getSyncedDate().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    setLogs((prev) => [newLog, ...prev].slice(0, 50)); // Keep last 50 logs
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return (
    <LogContext.Provider value={{ logs, addLog, clearLogs, isLogOpen, setIsLogOpen }}>
      {children}
    </LogContext.Provider>
  );
};
