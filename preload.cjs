// Electron preload script
// Expose safe APIs to the renderer window if needed in the future

const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  version: process.versions.electron
});
