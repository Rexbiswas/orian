import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, Sliders, Volume2, UserPlus, Sparkles } from 'lucide-react';
import axios from 'axios';

const VoiceCustomizer = () => {
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('D38z5RcWu1voky8WS1ja'); // Default
  const [settings, setSettings] = useState({
    stability: 0.5,
    similarity_boost: 0.75,
    style: 0.5,
    use_speaker_boost: true
  });

  useEffect(() => {
    fetchVoices();
  }, []);

  const fetchVoices = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/voice/list');
      setVoices(res.data.voices);
    } catch (err) {
      console.error("Failed to fetch voices");
    }
  };

  return (
    <div className="p-6 bg-slate-900/50 backdrop-blur-md border border-white/5 rounded-3xl space-y-6">
      <div className="flex items-center gap-3 border-b border-white/5 pb-4">
        <Sparkles size={20} className="text-brand-cyan" />
        <div>
          <h3 className="text-sm font-black uppercase tracking-widest text-white">Neural Voice Engine</h3>
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Voice Cloning & Emotional Synthesis</p>
        </div>
      </div>

      {/* Voice Selection */}
      <div className="space-y-3">
        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
          <Volume2 size={12} /> Select Identity
        </label>
        <div className="grid grid-cols-2 gap-2">
          {voices.slice(0, 4).map((voice) => (
            <button
              key={voice.voice_id}
              onClick={() => setSelectedVoice(voice.voice_id)}
              className={`p-3 rounded-xl border text-left transition-all ${
                selectedVoice === voice.voice_id 
                ? 'bg-brand-cyan/20 border-brand-cyan text-brand-cyan' 
                : 'bg-white/5 border-transparent text-slate-400 hover:border-white/10'
              }`}
            >
              <span className="text-[10px] font-black uppercase truncate block">{voice.name}</span>
              <span className="text-[8px] opacity-50 uppercase tracking-tighter">{voice.category}</span>
            </button>
          ))}
          <button className="p-3 rounded-xl border border-dashed border-white/10 flex items-center justify-center gap-2 text-slate-500 hover:text-white hover:border-white/30 transition-all">
            <UserPlus size={14} />
            <span className="text-[10px] font-black uppercase">Clone Voice</span>
          </button>
        </div>
      </div>

      {/* Neural Settings */}
      <div className="space-y-4">
        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
          <Sliders size={12} /> Acoustic Parameters
        </label>
        
        <NeuralSlider 
          label="Stability (Warmth)" 
          value={settings.stability} 
          onChange={(v) => setSettings({...settings, stability: v})} 
        />
        <NeuralSlider 
          label="Similarity (Authenticity)" 
          value={settings.similarity_boost} 
          onChange={(v) => setSettings({...settings, similarity_boost: v})} 
        />
        <NeuralSlider 
          label="Style (Expressiveness)" 
          value={settings.style} 
          onChange={(v) => setSettings({...settings, style: v})} 
        />
      </div>

      <div className="pt-4 border-t border-white/5">
        <div className="flex items-center justify-between px-2">
          <span className="text-[8px] font-bold text-slate-500 uppercase">Engine Status</span>
          <span className="text-[8px] font-black text-brand-cyan uppercase">Optimized</span>
        </div>
      </div>
    </div>
  );
};

const NeuralSlider = ({ label, value, onChange }) => (
  <div className="space-y-2">
    <div className="flex justify-between items-center">
      <span className="text-[9px] font-bold text-slate-500 uppercase tracking-tight">{label}</span>
      <span className="text-[9px] font-black text-brand-cyan">{Math.round(value * 100)}%</span>
    </div>
    <input 
      type="range" 
      min="0" 
      max="1" 
      step="0.01" 
      value={value} 
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-brand-cyan"
    />
  </div>
);

export default VoiceCustomizer;
