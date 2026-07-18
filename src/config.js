// Central API base configuration for Vercel vs Local development
const isLocal = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

export const API_BASE_URL = import.meta.env.VITE_API_URL || (isLocal ? 'http://127.0.0.1:8000' : '');
export const PROXY_BASE_URL = import.meta.env.VITE_PROXY_URL || (isLocal ? 'http://localhost:5000' : '');

export const WAKE_WORD = "hello orian";
export const ENABLE_WAKE_WORD = true;
