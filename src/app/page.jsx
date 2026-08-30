'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';

const GlobalLoading = () => (
  <div className="w-full h-screen bg-[#020611] flex flex-col items-center justify-center font-mono text-slate-400 select-none relative overflow-hidden">
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(138,43,226,0.1),transparent_70%)] pointer-events-none" />
    <div className="relative z-10 flex flex-col items-center gap-6 max-w-sm w-full px-6">
      <div className="w-48 h-20 border border-cyan-500/20 bg-[#020611]/80 backdrop-blur-md rounded-md p-3 relative flex items-center justify-center shadow-[0_0_30px_rgba(0,229,255,0.1)]">
        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-cyan-400" />
        <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-400" />
        <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-400" />
        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-cyan-400" />
        <div className="w-full h-full flex items-center justify-center text-cyan-400 font-bold tracking-widest text-[10px] animate-pulse">
          INITIALIZING ORIAN CORE...
        </div>
      </div>
      <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden relative border border-white/5">
        <motion.div
          initial={{ left: '-100%' }}
          animate={{ left: '100%' }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-0 bottom-0 w-1/2 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_8px_#00e5ff]"
        />
      </div>
    </div>
  </div>
);

const FirstPageLayout = dynamic(() => import('../layouts/FirstPageLayout'), {
  ssr: false,
  loading: () => <GlobalLoading />
});

export default function Home() {
  return (
    <main className="w-full h-screen h-dvh overflow-hidden bg-[#010208]">
      <FirstPageLayout />
    </main>
  );
}
