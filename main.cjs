const { app, BrowserWindow } = require('electron');
const path = require('path');
const child_process = require('child_process');

let mainWindow = null;
let nodeServerProcess = null;
let pythonProcess = null;
let hackerAIProcess = null;

// Track if processes are being shut down intentionally
let isQuitting = false;

// Kill process and all its children safely (especially on Windows)
function killProcess(proc, name) {
  if (!proc) return;
  console.log(`Terminating process tree for ${name} (PID ${proc.pid})...`);
  if (process.platform === 'win32') {
    try {
      child_process.execSync(`taskkill /pid ${proc.pid} /T /F`, { stdio: 'ignore' });
    } catch (e) {
      console.warn(`taskkill failed for ${name}, trying standard kill:`, e.message);
      proc.kill('SIGKILL');
    }
  } else {
    // Unix-like systems: kill group or standard kill
    try {
      proc.kill('SIGTERM');
    } catch (e) {
      proc.kill('SIGKILL');
    }
  }
}

// Clean up all sidecar processes
function cleanUpProcesses() {
  isQuitting = true;
  killProcess(nodeServerProcess, 'Node Proxy Server');
  killProcess(pythonProcess, 'Python Backend');
  killProcess(hackerAIProcess, 'HackerAI Bridge');
  
  nodeServerProcess = null;
  pythonProcess = null;
  hackerAIProcess = null;
}

// 1. Launch Node.js Proxy Server
function startNodeServer() {
  const nodeServerScript = app.isPackaged
    ? path.join(process.resourcesPath, 'server', 'index.js')
    : path.join(__dirname, 'server', 'index.js');

  console.log(`Starting Node Server at: ${nodeServerScript}`);

  nodeServerProcess = child_process.fork(nodeServerScript, [], {
    cwd: path.dirname(nodeServerScript),
    env: { ...process.env, PORT: '5000' }
  });

  nodeServerProcess.on('error', (err) => {
    console.error('Node Proxy Server failed to start:', err);
  });

  nodeServerProcess.on('close', (code) => {
    if (!isQuitting) {
      console.warn(`Node Proxy Server exited unexpectedly with code ${code}. Restarting...`);
      setTimeout(startNodeServer, 2000);
    }
  });
}

// 2. Launch Python FastAPI Backend (supporting multiple commands)
const pyCommands = ['python', 'python3', 'py'];
let pyCommandIndex = 0;

function startPythonBackend() {
  const pyScript = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'main.py')
    : path.join(__dirname, 'backend', 'main.py');

  if (pyCommandIndex >= pyCommands.length) {
    console.error('Failed to start Python: No python executable found in PATH');
    return;
  }

  const cmd = pyCommands[pyCommandIndex];
  console.log(`Starting Python Backend at ${pyScript} using command: ${cmd}`);

  const pyProc = child_process.spawn(cmd, [pyScript], {
    cwd: path.dirname(pyScript),
    env: { ...process.env }
  });

  pyProc.on('error', (err) => {
    if (err.code === 'ENOENT') {
      console.warn(`Command '${cmd}' not found. Trying next Python command...`);
      pyCommandIndex++;
      startPythonBackend();
    } else {
      console.error('Python Backend error:', err);
    }
  });

  pyProc.stdout.on('data', (data) => {
    console.log(`[Python Backend]: ${data.toString().trim()}`);
  });

  pyProc.stderr.on('data', (data) => {
    console.error(`[Python Backend Error]: ${data.toString().trim()}`);
  });

  pyProc.on('close', (code) => {
    if (!isQuitting && code !== 0) {
      console.warn(`Python Backend exited with code ${code}`);
    }
  });

  pythonProcess = pyProc;
}

// 3. Launch HackerAI Local Bridge
function startHackerAI() {
  console.log('Starting HackerAI Local Bridge...');
  
  const args = [
    '-y',
    '@hackerai/local@latest',
    '--token',
    'hsb_b14367f6b37d02aff7c5c964f4eb9799e2497de2de49f1daa88fcfde6f130465',
    '--name',
    'My Machine'
  ];

  hackerAIProcess = child_process.spawn('npx', args, {
    shell: true,
    env: { ...process.env }
  });

  hackerAIProcess.on('error', (err) => {
    console.error('HackerAI Bridge failed to start:', err);
  });

  hackerAIProcess.stdout.on('data', (data) => {
    console.log(`[HackerAI]: ${data.toString().trim()}`);
  });

  hackerAIProcess.stderr.on('data', (data) => {
    console.error(`[HackerAI Error]: ${data.toString().trim()}`);
  });

  hackerAIProcess.on('close', (code) => {
    if (!isQuitting && code !== 0) {
      console.warn(`HackerAI Bridge exited with code ${code}`);
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    title: 'OrionAI',
    backgroundColor: '#020617',
    icon: path.join(__dirname, 'assets/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    }
  });

  // Hide default menu
  mainWindow.setMenuBarVisibility(false);

  // Load URL depending on environment
  if (!app.isPackaged) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.on('ready', () => {
  // Start sidecars
  startNodeServer();
  startPythonBackend();
  startHackerAI();

  // Create UI
  createWindow();

  // Set macOS dock icon
  if (process.platform === 'darwin') {
    try {
      app.dock.setIcon(path.join(__dirname, 'assets/icon.png'));
    } catch (e) {
      console.warn('Failed to set macOS dock icon:', e.message);
    }
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  cleanUpProcesses();
});
