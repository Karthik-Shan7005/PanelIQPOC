// Preload runs in renderer context with Node access restricted.
// Expose only what the UI needs — nothing else.
const { contextBridge } = require('electron');

// Electron main passes the dynamic backend port via additionalArguments
const portArg = process.argv.find(a => a.startsWith('--paneliq-port='));
const backendPort = portArg ? parseInt(portArg.split('=')[1], 10) : 8000;

contextBridge.exposeInMainWorld('paneliqDesktop', {
  version: process.env.npm_package_version || '1.0.0',
  platform: process.platform,
  backendPort,
});
