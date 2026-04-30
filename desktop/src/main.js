const { app, BrowserWindow, dialog, shell, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const http = require('http');
const net = require('net');
const { spawn, spawnSync } = require('child_process');
const treeKill = require('tree-kill');

const DEFAULT_PORT = 8765;
const READINESS_TIMEOUT_MS = 30_000;
const PIP_INSTALL_TIMEOUT_MS = 10 * 60_000;

let backendProcess = null;
let backendLogStream = null;
let backendLogPath = null;
let mainWindow = null;
let isQuitting = false;

function getBackendRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }
  return path.resolve(__dirname, '..', '..');
}

function ensureUserDirs() {
  const userData = app.getPath('userData');
  const dataDir = path.join(userData, 'data');
  const logsDir = path.join(userData, 'logs');
  const runtimeDir = path.join(userData, 'runtime');
  fs.mkdirSync(dataDir, { recursive: true });
  fs.mkdirSync(logsDir, { recursive: true });
  fs.mkdirSync(runtimeDir, { recursive: true });
  return { dataDir, logsDir, runtimeDir };
}

function tryCommand(cmd, args) {
  try {
    const r = spawnSync(cmd, [...args, '--version'], { stdio: 'ignore' });
    return r.status === 0;
  } catch (_) {
    return false;
  }
}

function findSystemPython() {
  if (process.platform === 'win32') {
    if (tryCommand('py', ['-3'])) return { cmd: 'py', baseArgs: ['-3'] };
    if (tryCommand('python', [])) return { cmd: 'python', baseArgs: [] };
    if (tryCommand('python3', [])) return { cmd: 'python3', baseArgs: [] };
    return null;
  }
  if (tryCommand('python3', [])) return { cmd: 'python3', baseArgs: [] };
  if (tryCommand('python', [])) return { cmd: 'python', baseArgs: [] };
  return null;
}

function findDevPython(backendRoot) {
  const venvPython = process.platform === 'win32'
    ? path.join(backendRoot, 'venv', 'Scripts', 'python.exe')
    : path.join(backendRoot, 'venv', 'bin', 'python');
  if (fs.existsSync(venvPython)) return { cmd: venvPython, baseArgs: [] };
  return findSystemPython();
}

function venvPythonPath(venvDir) {
  return process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python');
}

function runProcess(cmd, args, options) {
  return new Promise((resolve, reject) => {
    backendLogStream.write(`\n$ ${cmd} ${args.join(' ')}\n`);
    const child = spawn(cmd, args, options);
    let timer = null;
    if (options && options.timeoutMs) {
      timer = setTimeout(() => {
        try { child.kill(); } catch (_) { /* noop */ }
      }, options.timeoutMs);
    }
    child.stdout.pipe(backendLogStream, { end: false });
    child.stderr.pipe(backendLogStream, { end: false });
    child.on('error', (err) => {
      if (timer) clearTimeout(timer);
      reject(err);
    });
    child.on('exit', (code, signal) => {
      if (timer) clearTimeout(timer);
      if (code === 0) resolve();
      else reject(new Error(`${path.basename(cmd)} ${args.join(' ')} a échoué (code=${code}, signal=${signal})`));
    });
  });
}

function hashRequirementsFile(requirementsPath) {
  const buf = fs.readFileSync(requirementsPath);
  return crypto.createHash('sha256').update(buf).digest('hex');
}

async function ensurePackagedVenv(backendRoot, runtimeDir) {
  const venvDir = path.join(runtimeDir, 'venv');
  const markerPath = path.join(runtimeDir, 'venv.requirements.sha256');
  const requirementsPath = path.join(backendRoot, 'requirements.txt');

  if (!fs.existsSync(requirementsPath)) {
    throw new Error(`requirements.txt introuvable dans ${backendRoot}`);
  }

  const venvPython = venvPythonPath(venvDir);
  const venvExists = fs.existsSync(venvPython);

  if (!venvExists) {
    const sysPython = findSystemPython();
    if (!sysPython) {
      throw new Error("Python introuvable sur le système. Installez Python 3.11+ depuis python.org puis relancez.");
    }
    backendLogStream.write(`bootstrap: création du venv runtime dans ${venvDir}\n`);
    try {
      await runProcess(sysPython.cmd, [...sysPython.baseArgs, '-m', 'venv', venvDir], {
        cwd: runtimeDir,
        env: process.env,
      });
    } catch (err) {
      throw new Error(`Création du venv runtime impossible : ${err.message}. Voir ${backendLogPath}`);
    }
    if (!fs.existsSync(venvPython)) {
      throw new Error(`Le venv runtime a été créé mais ${venvPython} est absent. Voir ${backendLogPath}`);
    }
  }

  const currentHash = hashRequirementsFile(requirementsPath);
  let storedHash = null;
  try { storedHash = fs.readFileSync(markerPath, 'utf8').trim(); } catch (_) { /* not present */ }

  if (!venvExists || storedHash !== currentHash) {
    backendLogStream.write(`bootstrap: installation des dépendances (${requirementsPath})\n`);
    try {
      await runProcess(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
        cwd: runtimeDir,
        env: process.env,
        timeoutMs: PIP_INSTALL_TIMEOUT_MS,
      });
      await runProcess(venvPython, ['-m', 'pip', 'install', '-r', requirementsPath], {
        cwd: runtimeDir,
        env: process.env,
        timeoutMs: PIP_INSTALL_TIMEOUT_MS,
      });
    } catch (err) {
      throw new Error(`Installation des dépendances Python échouée : ${err.message}. Voir ${backendLogPath}`);
    }
    fs.writeFileSync(markerPath, currentHash);
  }

  return { cmd: venvPython, baseArgs: [] };
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

function runMigrate(python, backendRoot, env) {
  return new Promise((resolve, reject) => {
    const args = [...python.baseArgs, 'manage.py', 'migrate', '--noinput'];
    backendLogStream.write(`\n$ ${python.cmd} ${args.join(' ')}\n`);
    const child = spawn(python.cmd, args, { cwd: backendRoot, env });
    child.stdout.pipe(backendLogStream, { end: false });
    child.stderr.pipe(backendLogStream, { end: false });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`migrate a échoué (code ${code}). Voir ${backendLogPath}`));
    });
  });
}

function spawnRunserver(python, backendRoot, port, env) {
  const args = [...python.baseArgs, 'manage.py', 'runserver', `127.0.0.1:${port}`, '--noreload'];
  backendLogStream.write(`\n$ ${python.cmd} ${args.join(' ')}\n`);
  const child = spawn(python.cmd, args, { cwd: backendRoot, env });
  child.stdout.pipe(backendLogStream, { end: false });
  child.stderr.pipe(backendLogStream, { end: false });
  return child;
}

async function startBackend() {
  const { dataDir, logsDir, runtimeDir } = ensureUserDirs();
  backendLogPath = path.join(logsDir, 'openasbl-backend.log');
  backendLogStream = fs.createWriteStream(backendLogPath, { flags: 'a' });
  backendLogStream.write(`\n--- ${new Date().toISOString()} session start (pid ${process.pid}) ---\n`);

  const backendRoot = getBackendRoot();
  backendLogStream.write(`backendRoot: ${backendRoot}\n`);
  backendLogStream.write(`packaged: ${app.isPackaged}\n`);

  let python;
  if (app.isPackaged) {
    python = await ensurePackagedVenv(backendRoot, runtimeDir);
  } else {
    python = findDevPython(backendRoot);
    if (!python) {
      const hint = process.platform === 'win32'
        ? 'Installez Python 3.11+ depuis python.org puis relancez.'
        : 'Installez python3 (ou créez le venv ./venv) puis relancez.';
      throw new Error(`Python introuvable. ${hint}`);
    }
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

  await runMigrate(python, backendRoot, env);

  backendProcess = spawnRunserver(python, backendRoot, port, env);
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
