import React, { useState, useEffect } from 'react';
import { 
  Clock, Calendar, Cpu, Zap, Activity, 
  Wifi, BatteryMedium, Radio, Globe, ShieldCheck, MapPin
} from 'lucide-react';
import { motion } from 'framer-motion';
import { syncTimeWithServer, getSyncedDate, isTimeSynced, getLastLatency } from '../utils/timeSync';

const StatItem = ({ icon: Icon, label, value, percent, color = "text-brand-cyan" }) => (
  <div className="flex flex-col items-end gap-1 px-4 border-r border-white/5 last:border-none group relative overflow-hidden">
    <div className="flex items-center gap-1.5 opacity-50 group-hover:opacity-100 transition-opacity">
      <motion.div
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <Icon size={10} className="text-slate-400" />
      </motion.div>
      <span className="text-[7px] font-black uppercase tracking-[0.2em] text-slate-500">{label}</span>
    </div>
    
    <div className="flex flex-col items-end">
      <div className={`text-[11px] font-mono font-bold ${color} glow-text-cyan tabular-nums`}>
        {value}
      </div>
      {/* Dynamic Mini-Bar */}
      <div className="w-12 h-0.5 bg-white/5 mt-1 rounded-full overflow-hidden">
        <motion.div 
          className={`h-full ${color.replace('text-', 'bg-')}`}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        />
      </div>
    </div>

    {/* Hover Glow Effect */}
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/2 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 pointer-events-none" />
  </div>
);

const Navbar = () => {
  const [time, setTime] = useState(getSyncedDate());
  const [deviceInfo, setDeviceInfo] = useState({ os: 'Loading...', browser: 'Detecting...' });
  const [systemData, setSystemData] = useState({
    cpu: 0,
    ram: 0,
    net: 0,
    latency: 0,
    battery: 0,
    cores: navigator.hardwareConcurrency || 8,
    isCharging: false,
    sync: "0.00"
  });
  const [location, setLocation] = useState('SYNCING_GEO...');
  const [coords, setCoords] = useState({ lat: 0, lng: 0 });

  useEffect(() => {
    // Detect Location - High Precision GPS
    const updateLocation = async (position) => {
      const { latitude, longitude } = position.coords;
      setCoords({ lat: latitude, lng: longitude });
      
      try {
        // Reverse geocode using a free API (OpenStreetMap/Nominatim)
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
        const data = await res.json();
        const city = data.address.city || data.address.town || data.address.village || data.address.suburb || 'UNKNOWN_STATION';
        const country = data.address.country_code?.toUpperCase() || 'XX';
        setLocation(`${city.toUpperCase()}, ${country}`);
      } catch (err) {
        setLocation(`${latitude.toFixed(4)}°N, ${longitude.toFixed(4)}°E`);
      }
    };

    const handleError = (error) => {
      console.warn("Location access denied or failed. Falling back to IP...");
      // Fallback to IP if GPS fails
      fetch('https://ipapi.co/json/')
        .then(res => res.json())
        .then(data => setLocation(`${data.city?.toUpperCase() || 'TERRA'}, ${data.country_code || 'ST'}`))
        .catch(() => setLocation('TERRA_STATION_01'));
    };

    if (navigator.geolocation) {
      const watchId = navigator.geolocation.watchPosition(updateLocation, handleError, {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      });
      return () => navigator.geolocation.clearWatch(watchId);
    } else {
      handleError();
    }
  }, []);

  useEffect(() => {
    // Detect OS and Browser
    const ua = navigator.userAgent;
    let os = "UNKNOWN_OS";
    const isDesktop = !/Mobi|Android/i.test(ua);

    if (ua.indexOf("Win") !== -1) os = "WINDOWS_X64";
    if (ua.indexOf("Mac") !== -1) os = "MACOS_ARM";
    if (ua.indexOf("Linux") !== -1) os = "LINUX_DISTRO";
    if (ua.indexOf("Android") !== -1) os = "ANDROID_OS";
    if (ua.indexOf("iPhone") !== -1) os = "IOS_MOBILE";

    const browser = ua.split(' ').pop().split('/')[0].toUpperCase();
    setDeviceInfo({ os, browser });

    let batteryInstance = null;

    const updateBatteryInfo = (battery) => {
      let level = Math.round(battery.level * 100);
      let charging = battery.charging;

      if (isDesktop && (level <= 0 || !isFinite(level))) {
        level = 100;
        charging = true;
      }

      setSystemData(prev => ({
        ...prev,
        battery: level,
        isCharging: charging
      }));
    };

    const initBattery = async () => {
      if (navigator.getBattery) {
        try {
          batteryInstance = await navigator.getBattery();
          updateBatteryInfo(batteryInstance);
          
          batteryInstance.addEventListener('chargingchange', () => updateBatteryInfo(batteryInstance));
          batteryInstance.addEventListener('levelchange', () => updateBatteryInfo(batteryInstance));
        } catch (e) {
          console.error("Battery API Error", e);
        }
      }
    };

    initBattery();

    // Initial Time Sync
    syncTimeWithServer();

    const updateStats = async () => {
      setTime(getSyncedDate());

      // 1. CPU
      const baseLoad = 15;
      const jitter = (Math.sin(Date.now() / 1500) * 5) + (Math.random() * 5);
      const cpuLoad = baseLoad + jitter;
      
      // 2. RAM
      let ramUsage = 0;
      if (window.performance && window.performance.memory) {
        ramUsage = (window.performance.memory.usedJSHeapSize / (1024 * 1024 * 1024)).toFixed(2);
      } else {
        const totalMem = navigator.deviceMemory || 8;
        ramUsage = (totalMem * 0.4 + Math.random() * 0.2).toFixed(2);
      }

      // 3. Network
      let netSpeed = 0;
      if (navigator.connection) {
        netSpeed = navigator.connection.downlink || 10;
      } else {
        netSpeed = 15 + Math.random() * 5;
      }

      // 4. Sync & Latency
      // Reflect actual sync status
      const syncRate = isTimeSynced() 
        ? 99.98 + (Math.random() * 0.01) 
        : 85.00 + (Math.random() * 5);

      setSystemData(prev => ({
        ...prev,
        cpu: cpuLoad.toFixed(1),
        ram: ramUsage,
        net: netSpeed.toFixed(1),
        latency: isTimeSynced() ? getLastLatency().toFixed(2) : (Math.random() * 5 + 10).toFixed(2),
        sync: syncRate.toFixed(2)
      }));
    };

    const timer = setInterval(updateStats, 1000); // 1s interval is enough for clock
    updateStats();
    
    // Refresh sync every 5 minutes
    const syncInterval = setInterval(syncTimeWithServer, 300000);
    
    return () => {
      clearInterval(timer);
      clearInterval(syncInterval);
      if (batteryInstance) {
        batteryInstance.removeEventListener('chargingchange', () => updateBatteryInfo(batteryInstance));
        batteryInstance.removeEventListener('levelchange', () => updateBatteryInfo(batteryInstance));
      }
    };
  }, []);

  return (
    <nav className="h-16 flex items-center justify-between px-8 border-b border-white/5 bg-black/40 backdrop-blur-xl z-50">
      {/* Logo Section */}
      <motion.div 
        className="flex items-center gap-3 group cursor-pointer"
        whileHover={{ scale: 1.02 }}
      >
        <div className="w-10 h-10 rounded-xl bg-brand-cyan/10 border border-brand-cyan/30 flex items-center justify-center text-brand-cyan shadow-[0_0_15px_rgba(0,242,255,0.2)] group-hover:shadow-[0_0_25px_rgba(0,242,255,0.5)] transition-all overflow-hidden relative">
          <Radio size={20} className="relative z-10" />
          <motion.div 
            className="absolute inset-0 bg-brand-cyan/20"
            animate={{ 
              opacity: [0.2, 0.5, 0.2],
              scale: [1, 1.5, 1]
            }}
            transition={{ duration: 3, repeat: Infinity }}
          />
        </div>
        <div className="flex flex-col">
          <span className="text-xl font-black tracking-tighter leading-none text-white group-hover:glow-text-cyan transition-all">
            ORIAN<span className="text-brand-cyan">AI</span>
          </span>
          <span className="text-[7px] font-black text-brand-cyan/60 uppercase tracking-[0.3em] mt-1 flex items-center gap-1">
            <ShieldCheck size={8} /> {deviceInfo.os}
          </span>
        </div>
      </motion.div>

      {/* Real-time System Stats */}
      <div className="hidden lg:flex items-center bg-white/[0.03] rounded-2xl px-2 py-1.5 border border-white/10 backdrop-blur-md">
        <StatItem 
          icon={Cpu} 
          label={`${systemData.cores} Core Load`} 
          value={`${systemData.cpu}%`} 
          percent={systemData.cpu}
        />
        <StatItem 
          icon={Zap} 
          label="Sync Rate" 
          value={`${systemData.sync}%`} 
          percent={(parseFloat(systemData.sync) - 99) * 100}
        />
        <StatItem 
          icon={Activity} 
          label="Mem Usage" 
          value={`${systemData.ram}GB`} 
          percent={(parseFloat(systemData.ram) / 16) * 100} 
          color="text-brand-purple" 
        />
        <StatItem 
          icon={Globe} 
          label={`${deviceInfo.browser} Net`} 
          value={`${systemData.net}Mb/s`} 
          percent={(parseFloat(systemData.net) / 100) * 100}
        />
        <StatItem 
          icon={systemData.isCharging ? Zap : BatteryMedium} 
          label={systemData.isCharging ? "Energy [PLUGGED]" : "Energy"} 
          value={`${systemData.battery}%`} 
          percent={systemData.battery}
          color={systemData.isCharging ? "text-brand-cyan" : "text-emerald-500"} 
        />
      </div>

      {/* Date and Time Section */}
      <div className="flex items-center gap-8">
        <motion.div 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => window.open(`https://www.google.com/maps?q=${coords.lat},${coords.lng}`, '_blank')}
          className="hidden xl:flex flex-col items-end gap-1 cursor-pointer group/loc"
        >
          <div className="flex items-center gap-2 text-[8px] font-black text-brand-cyan uppercase tracking-widest opacity-80 group-hover/loc:opacity-100 transition-opacity">
            <MapPin size={10} className="animate-bounce [animation-duration:2s]" />
            {location}
          </div>
          <div className="w-full h-[1px] bg-gradient-to-l from-brand-cyan/30 to-transparent group-hover/loc:from-brand-cyan transition-all" />
        </motion.div>

        <div className="hidden sm:flex flex-col items-end gap-1">
          <div className="flex items-center gap-2 text-[8px] font-black text-slate-500 uppercase tracking-widest opacity-70">
            <Calendar size={10} />
            {time.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }).toUpperCase()}
          </div>
          <div className="w-full h-[1px] bg-gradient-to-l from-brand-cyan/50 to-transparent" />
        </div>
        
        <div className="flex items-center gap-4 pl-8 border-l border-white/10">
          <div className="flex flex-col items-end">
            <motion.span 
              key={time.getSeconds()}
              initial={{ opacity: 0.8, y: -2 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-2xl font-black italic tracking-tighter text-white leading-none glow-text-cyan font-mono"
            >
              {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
            </motion.span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={`w-1.5 h-1.5 rounded-full ${isTimeSynced() ? 'bg-brand-cyan' : 'bg-amber-500'} animate-pulse shadow-[0_0_8px_${isTimeSynced() ? '#00f2ff' : '#f59e0b'}]`} />
              <span className="text-[7px] font-black text-slate-500 uppercase tracking-[0.2em]">
                {isTimeSynced() ? 'QUANTUM_TIME_SYNCED' : 'SYS_CLOCK_LOCAL'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
