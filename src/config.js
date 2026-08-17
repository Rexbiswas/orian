const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') return 'http://127.0.0.1:8000';
    if (host.startsWith('192.168.') || host.startsWith('10.') || host.startsWith('172.') || host.endsWith('.local')) {
      return `http://${host}:8000`;
    }
  }
  return '';
};

export const API_BASE_URL = getApiBaseUrl();
export const PROXY_BASE_URL = import.meta.env.VITE_PROXY_URL || (typeof window !== 'undefined' ? `http://${window.location.hostname}:5000` : '');

export const WAKE_WORD = "hello orian";
export const ENABLE_WAKE_WORD = true;
