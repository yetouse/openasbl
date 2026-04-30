const { contextBridge } = require('electron');

// Minimal, intentionally empty surface. Extend via ipcRenderer.invoke as
// concrete needs appear (e.g. open external folder, native dialogs).
contextBridge.exposeInMainWorld('openasbl', {
  platform: process.platform,
});
