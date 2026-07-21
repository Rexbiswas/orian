import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from 'lucide-react';

const NotificationToastSystem = ({ toasts = [], onRemove }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 size={16} className="text-emerald-400" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-amber-400" />;
      case 'error':
        return <XCircle size={16} className="text-rose-400" />;
      default:
        return <Info size={16} className="text-cyan-400" />;
    }
  };

  const getBorderColor = (type) => {
    switch (type) {
      case 'success':
        return 'border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)]';
      case 'warning':
        return 'border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.2)]';
      case 'error':
        return 'border-rose-500/40 shadow-[0_0_15px_rgba(244,63,94,0.2)]';
      default:
        return 'border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]';
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 50, scale: 0.9 }}
            transition={{ duration: 0.25 }}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/85 backdrop-blur-xl border ${getBorderColor(toast.type)} text-white`}
          >
            <div className="shrink-0 mt-0.5">{getIcon(toast.type)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-bold tracking-wide uppercase text-white/90 truncate">
                  {toast.title}
                </span>
                <span className="text-[9px] font-mono text-slate-400 shrink-0">
                  {toast.timestamp}
                </span>
              </div>
              <p className="text-[10.5px] text-slate-300 leading-snug mt-0.5 line-clamp-2">
                {toast.message}
              </p>
            </div>
            <button
              onClick={() => onRemove && onRemove(toast.id)}
              className="text-slate-500 hover:text-white transition-colors p-0.5 rounded shrink-0"
            >
              <X size={13} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default NotificationToastSystem;
