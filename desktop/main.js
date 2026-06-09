const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const BACKEND_PORT = 8000;
const isDev = !app.isPackaged;

let mainWindow = null;
let backendProcess = null;

// ── Path resolution: dev vs packaged ────────────────────────────────────────

function frontendIndexPath() {
  if (isDev) {
    return path.join(__dirname, '..', 'frontend', 'dist', 'index.html');
  }
  return path.join(process.resourcesPath, 'frontend', 'index.html');
}

// ── Backend lifecycle ────────────────────────────────────────────────────────

function startBackend() {
  return new Promise((resolve, reject) => {
    if (isDev) {
      // Dev: spawn uvicorn from the backend folder
      const backendDir = path.join(__dirname, '..', 'backend');
      backendProcess = spawn('uvicorn', ['main:app', '--port', String(BACKEND_PORT)], {
        cwd: backendDir,
        stdio: 'ignore',
        windowsHide: true,
        shell: true,       // needed on Windows so PATH is resolved
      });

      backendProcess.on('error', (err) => {
        reject(new Error(`Could not start uvicorn: ${err.message}\n\nMake sure uvicorn is installed:\n  pip install uvicorn`));
      });

      // Give uvicorn a moment to bind the port, then start polling
      setTimeout(() => pollBackend(resolve, reject, 30), 2000);
    } else {
      // Packaged: spawn compiled backend exe
      const exePath = path.join(process.resourcesPath, 'backend', 'paneliq_backend.exe');
      backendProcess = spawn(exePath, [], {
        stdio: 'ignore',
        windowsHide: true,
      });

      backendProcess.on('error', (err) => {
        reject(new Error(`Backend failed to launch: ${err.message}`));
      });

      setTimeout(() => pollBackend(resolve, reject, 30), 1500);
    }
  });
}

function pollBackend(resolve, reject, attemptsLeft) {
  if (attemptsLeft <= 0) {
    reject(new Error(
      'PanelIQ backend did not respond after 30 seconds.\n\n' +
      'This usually means:\n' +
      '• uvicorn is not installed  (run: pip install uvicorn fastapi)\n' +
      '• Port 8000 is blocked by another process\n\n' +
      'Note: Database queries require the BA network or VPN.'
    ));
    return;
  }

  const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/health`, (res) => {
    if (res.statusCode === 200) {
      resolve();
    } else {
      setTimeout(() => pollBackend(resolve, reject, attemptsLeft - 1), 1000);
    }
  });

  req.on('error', () => {
    setTimeout(() => pollBackend(resolve, reject, attemptsLeft - 1), 1000);
  });

  req.setTimeout(900, () => {
    req.destroy();
    setTimeout(() => pollBackend(resolve, reject, attemptsLeft - 1), 100);
  });
}

// ── Windows ──────────────────────────────────────────────────────────────────

function createLoadingWindow() {
  const win = new BrowserWindow({
    width: 420,
    height: 280,
    frame: false,
    resizable: false,
    center: true,
    backgroundColor: '#0a0d14',
    webPreferences: { nodeIntegration: false },
  });
  win.loadFile(path.join(__dirname, 'loading.html'));
  return win;
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    title: 'PanelIQ',
    backgroundColor: '#0a0d14',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(frontendIndexPath());
  mainWindow.setMenuBarVisibility(false);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  const loadingWin = createLoadingWindow();

  try {
    await startBackend();
    loadingWin.close();
    createMainWindow();
  } catch (err) {
    loadingWin.close();
    dialog.showErrorBox('PanelIQ — Startup Error', err.message);
    app.quit();
  }
});

function killBackend() {
  if (backendProcess) {
    try {
      // On Windows, kill the whole process tree so child processes don't linger
      if (process.platform === 'win32') {
        require('child_process').spawnSync('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t']);
      } else {
        backendProcess.kill('SIGTERM');
      }
    } catch (_) {}
    backendProcess = null;
  }
}

app.on('window-all-closed', () => {
  killBackend();
  app.quit();
});

app.on('before-quit', () => {
  killBackend();
});

// Safety net: ensure cleanup even on unexpected exit
process.on('exit', () => killBackend());
process.on('SIGINT',  () => { killBackend(); process.exit(0); });
process.on('SIGTERM', () => { killBackend(); process.exit(0); });
