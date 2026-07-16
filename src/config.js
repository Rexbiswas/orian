// Central API base configuration for Vercel vs Local development
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
export const PROXY_BASE_URL = import.meta.env.VITE_PROXY_URL || 'http://localhost:5000';
