// Preload runs in renderer context with Node access restricted.
// Expose only what the UI needs — nothing else.
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('paneliqDesktop', {
  version: process.env.npm_package_version || '1.0.0',
  platform: process.platform,
});
