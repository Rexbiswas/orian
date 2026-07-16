// Screen Wake Lock API wrapper to prevent mobile devices from sleeping during standby
export class WakeLockManager {
  constructor() {
    this.wakeLock = null;
  }

  async request() {
    if ('wakeLock' in navigator) {
      try {
        this.wakeLock = await navigator.wakeLock.request('screen');
        console.log('[WakeLock] Active: Screen standby prevented.');
        
        this.wakeLock.addEventListener('release', () => {
          console.log('[WakeLock] Released: Normal screen standby restored.');
        });
      } catch (err) {
        console.warn(`[WakeLock] Failed to request screen wake lock: ${err.message}`);
      }
    }
  }

  release() {
    if (this.wakeLock) {
      this.wakeLock.release();
      this.wakeLock = null;
    }
  }
}
