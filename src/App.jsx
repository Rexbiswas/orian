import React, { Suspense, Component } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { motion } from 'framer-motion';
import FirstPageLayout from './pages/FirstPageLayout';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="w-full h-screen bg-[#020611] flex flex-col items-center justify-center font-mono text-cyan-400 p-6 select-none">
          <div className="border border-cyan-500/40 bg-black/60 p-6 rounded-xl max-w-md w-full flex flex-col items-center gap-4 text-center">
            <span className="text-xs font-bold uppercase tracking-widest text-red-400">ORIAN CORE RECOVERY</span>
            <p className="text-[11px] text-slate-300">Neural layout encountered a runtime exception. Recovering interface...</p>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-cyan-500/20 border border-cyan-400/50 rounded text-xs font-bold hover:bg-cyan-500/40 transition-all cursor-pointer"
            >
              REINITIALIZE INTERFACE
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

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

function App() {
  return (
    <ErrorBoundary>
      <HashRouter>
        <Suspense fallback={<GlobalLoading />}>
          <Routes>
            <Route path="/" element={<FirstPageLayout />} />
          </Routes>
        </Suspense>
      </HashRouter>
    </ErrorBoundary>
  );
}

export default App;