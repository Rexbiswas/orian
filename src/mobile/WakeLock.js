// Screen Wake Lock API wrapper to prevent mobile devices from sleeping during standby
export class WakeLockManager {
  constructor() {
    this.wakeLock = null;
    this.isRequested = false;

    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && this.isRequested && !this.wakeLock) {
          this.request();
        }
      });
    }
  }

  async request() {
    this.isRequested = true;
    if (typeof navigator !== 'undefined' && 'wakeLock' in navigator && typeof document !== 'undefined') {
      if (document.visibilityState !== 'visible') {
        return;
      }
      try {
        if (!this.wakeLock) {
          this.wakeLock = await navigator.wakeLock.request('screen');
          this.wakeLock.addEventListener('release', () => {
            this.wakeLock = null;
          });
        }
      } catch (err) {
        // Silently ignore if page is not visible or policy restricted
      }
    }
  }

  release() {
    this.isRequested = false;
    if (this.wakeLock) {
      this.wakeLock.release().catch(() => {});
      this.wakeLock = null;
    }
  }
}
