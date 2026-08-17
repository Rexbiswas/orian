import React, { useState, useEffect, useRef } from 'react';
import { Clock, Cpu, Activity, Star, Globe, Bot, MapPin, Brain } from 'lucide-react';
import StatCard from '../system/StatCard';

const Header = ({ evolution = "68.4%" }) => {
  const [uptime, setUptime] = useState('00:00:00');
  const [telemetry, setTelemetry] = useState({ cpu: 28, ram: 54, gpu: 38, internet: 'Connected' });
  const [location, setLocation] = useState('NEW DELHI, IN');
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

  // Fetch location for Header telemetry
  useEffect(() => {
    const updateLocation = async (position) => {
      const { latitude, longitude } = position.coords;
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
        const data = await res.json();
        const city = data.address.city || data.address.town || data.address.village || data.address.suburb || 'UNKNOWN';
        const country = data.address.country_code?.toUpperCase() || 'IN';
        setLocation(`${city.toUpperCase()}, ${country}`);
      } catch (err) {
        setLocation(`${latitude.toFixed(2)}°N, ${longitude.toFixed(2)}°E`);
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(updateLocation, () => {
        fetch('https://ipapi.co/json/')
          .then(res => res.json())
          .then(data => {
            setLocation(`${data.city?.toUpperCase() || 'NEW DELHI'}, ${data.country_code || 'IN'}`);
          })
          .catch(() => {});
      });
    }
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
    <header className="h-14 flex items-center justify-between border border-blue-500/20 bg-[#020510]/90 rounded-xl px-4 backdrop-blur-xl relative overflow-hidden shadow-[0_0_30px_rgba(0,0,0,0.9),inset_0_1px_0_rgba(0,102,255,0.1)]">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/4 via-transparent to-green-400/3 pointer-events-none" />
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent pointer-events-none" />
      
      {/* Orian AI Logo */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-[0_0_15px_rgba(0,102,255,0.3)]">
            <Bot size={14} className="animate-pulse" />
          </div>
          <div className="absolute -inset-1 rounded-xl border border-blue-500/10 animate-pulse" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-black tracking-widest text-white leading-none">
            Orian <span className="text-blue-400">AI</span>
          </span>
          <span className="text-[6.5px] font-black text-slate-500 uppercase tracking-[0.4em] mt-1.5 leading-none">
            OS v2.0.1
          </span>
        </div>
      </div>

      {/* Telemetry metrics row */}
      <div className="hidden md:flex items-center bg-black/40 border border-blue-500/[0.12] rounded-xl py-1 px-2 backdrop-blur-sm gap-1">
        <StatCard icon={Clock} label="System Uptime" value={uptime} percentage={((Date.now() - bootTime.current) / 1000) % 60 / 60 * 100} color="text-cyan-400" glowColor="rgba(0, 229, 255, 0.4)" />
        <StatCard icon={Cpu} label="CPU Usage" value={`${telemetry.cpu}%`} percentage={telemetry.cpu} color="text-cyan-400" glowColor="rgba(0, 229, 255, 0.4)" />
        <StatCard icon={Activity} label="RAM Usage" value={`${telemetry.ram}%`} percentage={telemetry.ram} color="text-purple-400" glowColor="rgba(168, 85, 247, 0.4)" />
        <StatCard icon={Star} label="GPU Usage" value={`${telemetry.gpu}%`} percentage={telemetry.gpu} color="text-cyan-400" glowColor="rgba(0, 229, 255, 0.4)" />
        <StatCard icon={Globe} label="Internet" value={telemetry.internet} percentage={telemetry.internet === 'Connected' ? 100 : 0} color="text-emerald-400" glowColor="rgba(16, 185, 129, 0.4)" />
        <StatCard icon={MapPin} label="Location" value={location} percentage={100} color="text-blue-400" glowColor="rgba(0, 102, 255, 0.4)" />
        <StatCard icon={Bot} label="AI Agents" value="4 ONLINE" percentage={100} color="text-green-400" glowColor="rgba(0, 255, 136, 0.4)" />
        <StatCard icon={Brain} label="Brain Development" value={evolution} percentage={parseFloat(evolution) || 68.4} color="text-purple-400" glowColor="rgba(168, 85, 247, 0.4)" />
      </div>

      {/* Clock Display */}
      <div className="flex items-center gap-4 text-right">
        <div className="flex flex-col justify-center leading-none">
          <span className="text-[6.5px] font-black text-slate-500 uppercase tracking-widest leading-none mb-1">{formattedDate}</span>
          <span className="text-[6.5px] font-black text-blue-400/70 uppercase tracking-[0.2em] leading-none">{formattedDay}</span>
        </div>
        <div className="h-8 w-[1px] bg-white/10" />
        <span className="text-[16px] font-black tracking-tight text-white glow-text-blue tabular-nums leading-none">
          {formattedTime}
        </span>
      </div>
    </header>
  );
};

export default Header;
