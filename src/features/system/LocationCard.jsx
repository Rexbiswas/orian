import React, { useState, useEffect } from 'react';
import { MapPin } from 'lucide-react';

const LocationCard = () => {
  const [location, setLocation] = useState('NEW DELHI, INDIA');
  const [coords, setCoords] = useState({ lat: 28.6139, lng: 77.2090 });

  useEffect(() => {
    const updateLocation = async (position) => {
      const { latitude, longitude } = position.coords;
      setCoords({ lat: latitude, lng: longitude });
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
        const data = await res.json();
        const city = data.address.city || data.address.town || data.address.village || data.address.suburb || 'UNKNOWN_STATION';
        const country = data.address.country_code?.toUpperCase() || 'IN';
        setLocation(`${city.toUpperCase()}, ${country}`);
      } catch (err) {
        setLocation(`${latitude.toFixed(4)}°N, ${longitude.toFixed(4)}°E`);
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(updateLocation, () => {
        // Fallback using IP check
        fetch('https://ipapi.co/json/')
          .then(res => res.json())
          .then(data => {
            setLocation(`${data.city?.toUpperCase() || 'NEW DELHI'}, ${data.country_code || 'IN'}`);
            setCoords({ lat: data.latitude || 28.6139, lng: data.longitude || 77.2090 });
          })
          .catch(() => {});
      });
    }
  }, []);

  return (
    <div className="w-full lg:w-[32%] flex items-center gap-3.5 border-b lg:border-b-0 lg:border-r border-white/5 pb-2 lg:pb-0 pr-2 h-full min-w-0">
      <div className="w-9 h-9 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 shrink-0">
        <MapPin size={16} className="animate-bounce [animation-duration:3s]" />
      </div>
      <div className="flex flex-col justify-center min-w-0">
        <span className="text-[6.5px] font-black text-slate-500 uppercase tracking-widest mb-1.5 block">Location</span>
        <span className="text-[10px] font-bold text-white uppercase tracking-wider leading-none mb-1 truncate">
          {location}
        </span>
        <span className="text-[7.5px] font-mono text-cyan-400 leading-none font-bold">
          {coords.lat.toFixed(4)}° {coords.lat >= 0 ? 'N' : 'S'}, {coords.lng.toFixed(4)}° {coords.lng >= 0 ? 'E' : 'W'}
        </span>
      </div>
    </div>
  );
};

export default LocationCard;
