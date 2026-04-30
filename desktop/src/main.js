const { app, BrowserWindow, dialog, shell, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const net = require('net');
const { spawn, spawnSync } = require('child_process');
const treeKill = require('tree-kill');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_PORT = 8765;
const READINESS_TIMEOUT_MS = 30_000;

let backendProcess = null;
let backendLogStream = null;
let backendLogPath = null;
let mainWindow = null;
let isQuitting = false;

function ensureUserDirs() {
  const userData = app.getPath('userData');
  const dataDir = path.join(userData, 'data');
  const logsDir = path.join(userData, 'logs');
  fs.mkdirSync(dataDir, { recursive: true });
  fs.mkdirSync(logsDir, { recursive: true });
  return { dataDir, logsDir };
}

function tryCommand(cmd, args) {
  try {
    const r = spawnSync(cmd, [...args, '--version'], { stdio: 'ignore' });
    return r.status === 0;
  } catch (_) {
    return false;
  }
}

function findPython() {
  if (process.platform === 'win32') {
    if (tryCommand('py', ['-3'])) return { cmd: 'py', baseArgs: ['-3'] };
    if (tryCommand('python', [])) return { cmd: 'python', baseArgs: [] };
    if (tryCommand('python3', [])) return { cmd: 'python3', baseArgs: [] };
    return null;
  }
  const venvPython = path.join(REPO_ROOT, 'venv', 'bin', 'python');
  if (fs.existsSync(venvPython)) return { cmd: venvPython, baseArgs: [] };
  if (tryCommand('python3', [])) return { cmd: 'python3', baseArgs: [] };
  if (tryCommand('python', [])) return { cmd: 'python', baseArgs: [] };
  return null;
}

function isPortFree(port) {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.once('error', () => {
      try { srv.close(); } catch (_) { /* noop */ }
      resolve(false);
    });
    srv.once('listening', () => srv.close(() => resolve(true)));
    srv.listen(port, '127.0.0.1');
  });
}

function pickFreePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.unref();
    srv.once('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

async function selectPort() {
  if (await isPortFree(DEFAULT_PORT)) return DEFAULT_PORT;
  return pickFreePort();
}

function waitForHttp(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const tick = () => {
      if (backendProcess === null) {
        reject(new Error('backend exited before becoming ready'));
        return;
      }
      const req = http.get(url, (res) => {
        res.resume();
        resolve();
      });
      req.on('error', () => {
        if (Date.now() > deadline) {
          reject(new Error(`Timeout en attendant ${url}`));
        } else {
          setTimeout(tick, 250);
        }
      });
      req.setTimeout(2000, () => req.destroy());
    };
    tick();
  });
}

function runMigrate(python, env) {
  return new Promise((resolve, reject) => {
    const args = [...python.baseArgs, 'manage.py', 'migrate', '--noinput'];
    backendLogStream.write(`\n$ ${python.cmd} ${args.join(' ')}\n`);
    const child = spawn(python.cmd, args, { cwd: REPO_ROOT, env });
    child.stdout.pipe(backendLogStream, { end: false });
    child.stderr.pipe(backendLogStream, { end: false });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`migrate a échoué (code ${code}). Voir ${backendLogPath}`));
    });
  });
}

function spawnRunserver(python, port, env) {
  const args = [...python.baseArgs, 'manage.py', 'runserver', `127.0.0.1:${port}`, '--noreload'];
  backendLogStream.write(`\n$ ${python.cmd} ${args.join(' ')}\n`);
  const child = spawn(python.cmd, args, { cwd: REPO_ROOT, env });
  child.stdout.pipe(backendLogStream, { end: false });
  child.stderr.pipe(backendLogStream, { end: false });
  return child;
}

async function startBackend() {
  const { dataDir, logsDir } = ensureUserDirs();
  backendLogPath = path.join(logsDir, 'openasbl-backend.log');
  backendLogStream = fs.createWriteStream(backendLogPath, { flags: 'a' });
  backendLogStream.write(`\n--- ${new Date().toISOString()} session start (pid ${process.pid}) ---\n`);

  const python = findPython();
  if (!python) {
    const hint = process.platform === 'win32'
      ? 'Installez Python 3.11+ depuis python.org puis relancez.'
      : 'Installez python3 (ou créez le venv ./venv) puis relancez.';
    throw new Error(`Python introuvable. ${hint}`);
  }
  backendLogStream.write(`python: ${python.cmd} ${python.baseArgs.join(' ')}\n`);

  const port = await selectPort();
  const env = {
    ...process.env,
    OPENASBL_RUNTIME_MODE: 'desktop',
    OPENASBL_DATA_DIR: dataDir,
    OPENASBL_PORT: String(port),
    PYTHONUNBUFFERED: '1',
  };

  await runMigrate(python, env);

  backendProcess = spawnRunserver(python, port, env);
  backendProcess.on('error', (err) => {
    backendLogStream && backendLogStream.write(`backend spawn error: ${err.message}\n`);
  });
  backendProcess.on('exit', (code, signal) => {
    backendLogStream && backendLogStream.write(`backend exited code=${code} signal=${signal}\n`);
    backendProcess = null;
    if (!isQuitting) {
      dialog.showErrorBox(
        'OpenASBL',
        `Le backend Django s'est arrêté de manière inattendue (code=${code}, signal=${signal}).\nJournal : ${backendLogPath}`,
      );
      app.quit();
    }
  });

  await waitForHttp(`http://127.0.0.1:${port}/`, READINESS_TIMEOUT_MS);
  return port;
}

function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 600,
    title: 'OpenASBL',
    backgroundColor: '#ffffff',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  Menu.setApplicationMenu(null);

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    try {
      const target = new URL(url);
      if (target.hostname !== '127.0.0.1' && target.hostname !== 'localhost') {
        event.preventDefault();
        shell.openExternal(url);
      }
    } catch (_) {
      event.preventDefault();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.loadURL(`http://127.0.0.1:${port}/`);
}

function killBackend() {
  if (backendProcess && backendProcess.pid) {
    const pid = backendProcess.pid;
    backendProcess = null;
    try {
      treeKill(pid);
    } catch (_) { /* noop */ }
  }
  if (backendLogStream) {
    try {
      backendLogStream.end(`--- ${new Date().toISOString()} session end ---\n`);
    } catch (_) { /* noop */ }
    backendLogStream = null;
  }
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    try {
      const port = await startBackend();
      createWindow(port);
    } catch (err) {
      dialog.showErrorBox(
        'OpenASBL — démarrage impossible',
        `${err.message}\n\nJournal : ${backendLogPath ?? '(non créé)'}`,
      );
      isQuitting = true;
      killBackend();
      app.quit();
    }
  });

  app.on('window-all-closed', () => {
    isQuitting = true;
    killBackend();
    if (process.platform !== 'darwin') app.quit();
  });

  app.on('before-quit', () => {
    isQuitting = true;
    killBackend();
  });

  process.on('exit', killBackend);
}
