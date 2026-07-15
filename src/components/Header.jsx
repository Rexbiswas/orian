import React, { useState, useEffect, useRef } from 'react';
import { Clock, Cpu, Activity, Star, Globe, Bot } from 'lucide-react';
import StatCard from './StatCard';

const Header = ({ evolution = "68.4%" }) => {
  const [uptime, setUptime] = useState('00:00:00');
  const [telemetry, setTelemetry] = useState({ cpu: 28, ram: 54, gpu: 38, internet: 'Connected' });
  const bootTime = useRef(Date.now());

  // Setup uptime counter and load fluctuations
  useEffect(() => {
    const timer = setInterval(() => {
      const diff = Date.now() - bootTime.current;
      const hrs = String(Math.floor(diff / 3600000)).padStart(2, '0');
      const mins = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0');
      const secs = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
      setUptime(`${hrs}:${mins}:${secs}`);

      setTelemetry({
        cpu: Math.max(12, Math.min(88, Math.round(34 + Math.sin(Date.now() / 3000) * 8 + Math.random() * 4))),
        ram: Math.max(45, Math.min(75, Math.round(62 + Math.sin(Date.now() / 8000) * 1))),
        gpu: Math.max(15, Math.min(95, Math.round(48 + Math.cos(Date.now() / 4000) * 12 + Math.random() * 3))),
        internet: 'Connected'
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const [timeState, setTimeState] = useState(new Date());
  useEffect(() => {
    const clock = setInterval(() => setTimeState(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  const formattedTime = timeState.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  const formattedDay = timeState.toLocaleDateString([], { weekday: 'long' });
  const formattedDate = timeState.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <header className="h-14 flex items-center justify-between border border-cyan-400/15 bg-black/60 rounded-lg px-4 backdrop-blur-md relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/5 via-transparent to-purple-600/5 pointer-events-none" />
      
      {/* HUMAINOD AI Logo info */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-cyan-400/10 border border-cyan-400/35 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(0,229,255,0.2)]">
          <Bot size={14} className="animate-pulse" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-black tracking-widest text-white leading-none">
            HUMAINOD <span className="text-cyan-400">AI</span>
          </span>
          <span className="text-[6.5px] font-black text-slate-400 uppercase tracking-[0.4em] mt-1.5 leading-none">
            OS v2.0
          </span>
        </div>
      </div>

      {/* Telemetry metrics row */}
      <div className="hidden md:flex items-center bg-white/[0.02] border border-white/5 rounded-lg py-1 px-1.5 backdrop-blur-sm">
        <StatCard icon={Clock} label="System Uptime" value={uptime} color="text-cyan-400" />
        <StatCard icon={Cpu} label="CPU Usage" value={`${telemetry.cpu}%`} color="text-cyan-400" />
        <StatCard icon={Activity} label="RAM Usage" value={`${telemetry.ram}%`} color="text-purple-400" />
        <StatCard icon={Star} label="GPU Usage" value={`${telemetry.gpu}%`} color="text-cyan-400" />
        <StatCard icon={Globe} label="Internet" value={telemetry.internet} color="text-emerald-400" />
      </div>

      {/* Clock Display */}
      <div className="flex items-center gap-4 text-right">
        <div className="flex flex-col justify-center leading-none">
          <span className="text-[7.5px] font-black text-slate-500 uppercase tracking-widest leading-none mb-1">{formattedDate}</span>
          <span className="text-[7.5px] font-black text-cyan-400/70 uppercase tracking-[0.2em] leading-none">{formattedDay}</span>
        </div>
        <div className="h-8 w-[1px] bg-white/10" />
        <span className="text-[17px] font-black tracking-tight text-white glow-text-cyan tabular-nums leading-none">
          {formattedTime}
        </span>
      </div>
    </header>
  );
};

export default Header;
