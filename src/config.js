export const getEnvVar = (name) => {
  if (typeof process !== 'undefined' && process.env) {
    if (process.env[name]) return process.env[name];
    if (process.env[`NEXT_PUBLIC_${name}`]) return process.env[`NEXT_PUBLIC_${name}`];
    if (name.startsWith('VITE_') && process.env[`NEXT_PUBLIC_${name.replace('VITE_', '')}`]) {
      return process.env[`NEXT_PUBLIC_${name.replace('VITE_', '')}`];
    }
  }
  try {
    if (typeof import.meta !== 'undefined' && import.meta?.env) {
      if (import.meta.env[name]) return import.meta.env[name];
    }
  } catch (e) {}
  return undefined;
};

const getApiBaseUrl = () => {
  const customUrl = getEnvVar('VITE_API_URL') || getEnvVar('API_URL');
  if (customUrl) return customUrl;
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
export const WS_BASE_URL = API_BASE_URL ? API_BASE_URL.replace(/^http/, 'ws') : (typeof window !== 'undefined' ? `ws://${window.location.host}` : '');
export const PROXY_BASE_URL = getEnvVar('VITE_PROXY_URL') || getEnvVar('PROXY_URL') || (typeof window !== 'undefined' ? `http://${window.location.hostname}:5000` : '');

export const WAKE_WORD = "hello orian";
export const ENABLE_WAKE_WORD = true;
