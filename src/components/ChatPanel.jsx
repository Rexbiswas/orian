import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Terminal, Cpu, Sparkles, X, Command } from 'lucide-react';
import { useLogs } from '../context/LogContext';


const ChatPanel = ({ onClose }) => {
  const [messages, setMessages] = useState([
    { id: 1, role: 'ai', text: 'Hello Master! i am orian, your personal ai assistant. How can i help you today?' }
  ]);
   const [input, setInput] = useState('');
   const [isTyping, setIsTyping] = useState(false);
   const { addLog } = useLogs();
   const scrollRef = useRef(null);


  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg = { id: Date.now(), role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    addLog(`INIT_QUERY: "${input}"`, 'EXEC', 'INFO');
    addLog(`SEARCHING_NEURAL_NODES...`, 'NET', 'INFO');

    // Simulate AI response
    setTimeout(() => {
      const responseText = `Processing query: "${input}". Accessing quantum databases... Request synchronized.`;
      const aiMsg = { 
        id: Date.now() + 1, 
        role: 'ai', 
        text: responseText 
      };
      setMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
      
      addLog(`RESPONSE_SYNCED`, 'SYS', 'SUCCESS');
      addLog(`DATA_RECALIBRATED`, 'MEM', 'INFO');
    }, 1500);
  };


  return (
    <div className="w-80 h-96 glass-morphism rounded-2xl flex flex-col overflow-hidden border border-brand-cyan/20 shadow-[0_0_20px_rgba(0,242,255,0.1)]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 bg-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-brand-cyan" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Neural_Chat</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <button 
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-md text-slate-500 hover:text-brand-cyan transition-all"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar"
      >
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, x: msg.role === 'user' ? 10 : -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className={`max-w-[90%] px-3 py-2 rounded-xl text-[11px] font-medium leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-brand-cyan/20 border border-brand-cyan/30 text-white' 
                  : 'bg-white/5 border border-white/10 text-slate-300'
              }`}>
                {msg.text}
              </div>
              <span className="text-[7px] font-bold text-slate-600 uppercase tracking-widest mt-1">
                {msg.role === 'ai' ? 'Orian_OS' : 'Admin'}
              </span>
            </motion.div>
          ))}
          
          {isTyping && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2"
            >
              <div className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 flex gap-1 items-center">
                <div className="w-1 h-1 bg-brand-cyan rounded-full animate-bounce" />
                <div className="w-1 h-1 bg-brand-cyan rounded-full animate-bounce [animation-delay:200ms]" />
                <div className="w-1 h-1 bg-brand-cyan rounded-full animate-bounce [animation-delay:400ms]" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/5 bg-white/2">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Initialize neural query..."
            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-[11px] text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-cyan/40 transition-all"
          />
          <button 
            onClick={handleSend}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-600 hover:text-brand-cyan transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
