import React from 'react';
import { Send } from 'lucide-react';
import GlassCard from './GlassCard';
import { playButtonClick } from '../utils/sound';

const TextCommand = ({ input, setInput, handleSend }) => {
  return (
    <GlassCard title="TEXT COMMAND" className="w-full lg:w-[44%] flex flex-col p-3 justify-center relative overflow-hidden">
      <div className="relative w-full flex items-center pt-0.5">
        <div className="absolute left-3 text-cyan-400/40 text-[9px] font-mono pointer-events-none select-none">&gt;</div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') { playButtonClick(); handleSend(); }
          }}
          placeholder="Type your command here..."
          className="hud-input w-full pl-6 pr-10 py-2.5 text-[10px]"
        />
        <button
          onClick={() => { playButtonClick(); handleSend(); }}
          className="absolute right-3 w-6 h-6 flex items-center justify-center rounded-md bg-cyan-400/10 hover:bg-cyan-400/20 text-cyan-400 hover:text-cyan-200 transition-all shadow-[0_0_8px_rgba(0,229,255,0.25)] hover:shadow-[0_0_14px_rgba(0,229,255,0.45)]"
        >
          <Send size={11} />
        </button>
      </div>
    </GlassCard>
  );
};

export default TextCommand;
