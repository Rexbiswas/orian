import React from 'react';
import { Send } from 'lucide-react';
import GlassCard from './GlassCard';

const TextCommand = ({ input, setInput, handleSend }) => {
  return (
    <GlassCard title="TEXT COMMAND" className="w-[44%] flex flex-col p-3 justify-center relative overflow-hidden">
      <div className="relative w-full flex items-center pt-0.5">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your command here..."
          className="w-full bg-[#07051a]/60 border border-cyan-400/20 rounded-lg px-4 py-2.5 text-[10px] text-white placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/45 transition-all font-mono"
        />
        <button 
          onClick={() => handleSend()}
          className="absolute right-3.5 text-cyan-400 hover:text-cyan-200 transition-colors shadow-[0_0_10px_rgba(0,229,255,0.4)]"
        >
          <Send size={13} />
        </button>
      </div>
    </GlassCard>
  );
};

export default TextCommand;
