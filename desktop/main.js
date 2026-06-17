const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const net  = require('net');

const isDev = !app.isPackaged;

let mainWindow    = null;
let backendProcess = null;
let backendPort   = 8000;

// ── Single-instance lock ──────────────────────────────────────────────────────
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// ── Path resolution: dev vs packaged ─────────────────────────────────────────

function frontendIndexPath() {
  if (isDev) {
    return path.join(__dirname, '..', 'frontend', 'dist', 'index.html');
  }
  return path.join(process.resourcesPath, 'frontend', 'index.html');
}

// ── Free port detection ───────────────────────────────────────────────────────

function getFreePort() {
  return new Promise((resolve) => {
    const srv = net.createServer().listen(0, '127.0.0.1', () => {
      const port = srv.address().port;
      srv.close(() => resolve(port));
    });
  });
}

// ── Backend lifecycle ─────────────────────────────────────────────────────────

async function startBackend() {
  backendPort = await getFreePort();

  return new Promise((resolve, reject) => {
    if (isDev) {
      const backendDir = path.join(__dirname, '..', 'backend');
      const py = process.env.PANELIQ_PYTHON ||
        'C:\\Users\\KarthikShanmugam\\.anaconda\\envs\\paneliq\\python.exe';

      backendProcess = spawn(
        py,
        ['-m', 'uvicorn', 'main:app', '--port', String(backendPort)],
        { cwd: backendDir, stdio: 'ignore', windowsHide: true }
      );
    } else {
      const exePath = path.join(process.resourcesPath, 'backend', 'paneliq_backend.exe');
      backendProcess = spawn(exePath, ['--port', String(backendPort)], {
        stdio: 'ignore',
        windowsHide: true,
      });
    }

    backendProcess.on('error', (err) => {
      reject(new Error(`Backend failed to launch: ${err.message}`));
    });

    // Fail fast if the exe crashes immediately instead of waiting 30 s
    backendProcess.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        reject(new Error(
          `PanelIQ backend crashed on startup (exit code ${code}).\n\n` +
          `Check the diagnostic log at:\n` +
          `  %LOCALAPPDATA%\\PanelIQ\\logs\\backend.log`
        ));
      }
    });

    setTimeout(() => pollBackend(resolve, reject, Date.now() + 30_000), 500);
  });
}

function pollBackend(resolve, reject, deadlineMs) {
  if (Date.now() > deadlineMs) {
    reject(new Error(
      'PanelIQ backend did not respond within 30 seconds.\n\n' +
      'Common causes:\n' +
      '  • ODBC Driver 17 for SQL Server is not installed\n' +
      '  • An antivirus blocked paneliq_backend.exe\n' +
      '  • The paneliq.env config file is missing from %APPDATA%\\PanelIQ\\\n\n' +
      'Diagnostic log: %LOCALAPPDATA%\\PanelIQ\\logs\\backend.log\n\n' +
      'Note: Database queries require the BA network or VPN.'
    ));
    return;
  }

  const req = http.get(`http://127.0.0.1:${backendPort}/health`, (res) => {
    if (res.statusCode === 200) {
      resolve();
    } else {
      setTimeout(() => pollBackend(resolve, reject, deadlineMs), 500);
    }
  });

  req.on('error', () => setTimeout(() => pollBackend(resolve, reject, deadlineMs), 500));
  req.setTimeout(800, () => { req.destroy(); });
}

// ── Windows ───────────────────────────────────────────────────────────────────

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
      additionalArguments: [`--paneliq-port=${backendPort}`],
    },
  });

  mainWindow.loadFile(frontendIndexPath());
  mainWindow.setMenuBarVisibility(false);

  mainWindow.on('closed', () => { mainWindow = null; });
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

// ── Process cleanup ───────────────────────────────────────────────────────────

function killBackend() {
  if (!backendProcess) return;
  const pid = backendProcess.pid;
  backendProcess = null;
  if (process.platform === 'win32') {
    // /t kills the full process tree — required when shell:true spawns cmd.exe
    require('child_process')
      .spawn('taskkill', ['/pid', String(pid), '/f', '/t'],
        { detached: true, stdio: 'ignore' })
      .unref();
  } else {
    try { process.kill(pid, 'SIGTERM'); } catch (_) {}
  }
}

app.on('window-all-closed', () => { killBackend(); app.quit(); });
app.on('before-quit',       () => { killBackend(); });
process.on('exit',   () => killBackend());
process.on('SIGINT',  () => { killBackend(); process.exit(0); });
process.on('SIGTERM', () => { killBackend(); process.exit(0); });
