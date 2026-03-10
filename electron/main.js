const { app, BrowserWindow, ipcMain, Menu, shell, dialog } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn, execSync } = require("child_process");
const os = require("os");

const isDev = process.argv.includes("--dev");

function getResourcePath(...segments) {
  if (isDev || !app.isPackaged) {
    return path.join(__dirname, "..", ...segments);
  }
  return path.join(process.resourcesPath, ...segments);
}

function getOpenClawDir() {
  return process.env.OPENCLAW_STATE_DIR || path.join(os.homedir(), ".openclaw");
}

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 480,
    height: 860,
    minWidth: 380,
    minHeight: 600,
    title: "ClawRecord",
    backgroundColor: "#f7f7f7",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    titleBarStyle: process.platform === "darwin" ? "hiddenInset" : "default",
    trafficLightPosition: { x: 12, y: 12 },
  });

  mainWindow.loadFile(path.join(__dirname, "..", "docs", "index.html"));

  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: "detach" });
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function buildAppMenu() {
  const template = [
    ...(process.platform === "darwin"
      ? [
          {
            label: app.name,
            submenu: [
              { role: "about" },
              { type: "separator" },
              { role: "services" },
              { type: "separator" },
              { role: "hide" },
              { role: "hideOthers" },
              { role: "unhide" },
              { type: "separator" },
              { role: "quit" },
            ],
          },
        ]
      : []),
    {
      label: "File",
      submenu: [
        {
          label: "Refresh Data",
          accelerator: "CmdOrCtrl+R",
          click: () => mainWindow?.webContents.send("trigger-refresh"),
        },
        { type: "separator" },
        process.platform === "darwin" ? { role: "close" } : { role: "quit" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    {
      label: "Help",
      submenu: [
        {
          label: "ClawRecord on GitHub",
          click: () =>
            shell.openExternal("https://github.com/luka2chat/clawrecord"),
        },
        {
          label: "OpenClaw on GitHub",
          click: () =>
            shell.openExternal("https://github.com/openclaw/openclaw"),
        },
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ── IPC Handlers ────────────────────────────────────────────────

function runPythonScript(scriptName, args = []) {
  return new Promise((resolve, reject) => {
    const scriptPath = getResourcePath("scripts", scriptName);
    if (!fs.existsSync(scriptPath)) {
      return reject(new Error(`Script not found: ${scriptPath}`));
    }

    const python = findPython();
    if (!python) {
      return reject(
        new Error("Python 3 not found. Please install Python 3.8+.")
      );
    }

    const child = spawn(python, [scriptPath, ...args], {
      cwd: getResourcePath(),
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    child.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`Script ${scriptName} exited with code ${code}: ${stderr}`));
      }
    });

    child.on("error", (err) => reject(err));
  });
}

function findPython() {
  const candidates =
    process.platform === "win32"
      ? ["python", "python3", "py"]
      : ["python3", "python"];

  for (const cmd of candidates) {
    try {
      const version = execSync(`${cmd} --version`, {
        encoding: "utf-8",
        timeout: 5000,
      }).trim();
      if (version.includes("Python 3")) {
        return cmd;
      }
    } catch {
      // continue
    }
  }
  return null;
}

function checkOpenClawInstalled() {
  const openClawDir = getOpenClawDir();
  const configPath = path.join(openClawDir, "config.json");
  const sessionsDir = path.join(openClawDir, "agents", "main", "sessions");

  return {
    installed: fs.existsSync(openClawDir),
    hasConfig: fs.existsSync(configPath),
    hasSessions: fs.existsSync(sessionsDir),
    path: openClawDir,
  };
}

function detectOpenClawBinary() {
  const candidates =
    process.platform === "win32"
      ? ["openclaw.exe", "openclaw"]
      : ["openclaw"];

  for (const cmd of candidates) {
    try {
      const result = execSync(`which ${cmd} 2>/dev/null || where ${cmd} 2>nul`, {
        encoding: "utf-8",
        timeout: 5000,
      }).trim();
      if (result) return result;
    } catch {
      // continue
    }
  }

  const npmGlobalPaths = [
    path.join(os.homedir(), ".npm-global", "bin", "openclaw"),
    path.join(os.homedir(), ".local", "bin", "openclaw"),
    "/usr/local/bin/openclaw",
    "/usr/bin/openclaw",
  ];
  if (process.platform === "win32") {
    npmGlobalPaths.push(
      path.join(
        process.env.APPDATA || "",
        "npm",
        "openclaw.cmd"
      )
    );
  }

  for (const p of npmGlobalPaths) {
    if (fs.existsSync(p)) return p;
  }

  return null;
}

function installOpenClaw() {
  return new Promise((resolve, reject) => {
    const packageManagers = [];

    try {
      execSync("npm --version", { encoding: "utf-8", timeout: 5000 });
      packageManagers.push({ cmd: "npm", args: ["install", "-g", "openclaw"] });
    } catch {
      // npm not found
    }

    try {
      execSync("pnpm --version", { encoding: "utf-8", timeout: 5000 });
      packageManagers.push({ cmd: "pnpm", args: ["add", "-g", "openclaw"] });
    } catch {
      // pnpm not found
    }

    try {
      execSync("yarn --version", { encoding: "utf-8", timeout: 5000 });
      packageManagers.push({ cmd: "yarn", args: ["global", "add", "openclaw"] });
    } catch {
      // yarn not found
    }

    if (process.platform !== "win32") {
      try {
        execSync("brew --version", { encoding: "utf-8", timeout: 5000 });
        packageManagers.push({ cmd: "brew", args: ["install", "openclaw"] });
      } catch {
        // brew not found
      }
    }

    if (packageManagers.length === 0) {
      return reject(
        new Error(
          "No supported package manager found (npm, pnpm, yarn, brew). Please install Node.js/npm first."
        )
      );
    }

    const pm = packageManagers[0];
    const child = spawn(pm.cmd, pm.args, {
      env: { ...process.env },
      shell: true,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (d) => {
      stdout += d.toString();
      mainWindow?.webContents.send("install-progress", {
        type: "stdout",
        data: d.toString(),
      });
    });

    child.stderr.on("data", (d) => {
      stderr += d.toString();
      mainWindow?.webContents.send("install-progress", {
        type: "stderr",
        data: d.toString(),
      });
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve({
          success: true,
          method: `${pm.cmd} ${pm.args.join(" ")}`,
          stdout,
        });
      } else {
        reject(
          new Error(
            `Installation failed (${pm.cmd}): exit code ${code}\n${stderr}`
          )
        );
      }
    });

    child.on("error", (err) => reject(err));
  });
}

function installHook() {
  return new Promise((resolve, reject) => {
    const hookSrc = getResourcePath("hooks", "clawrecord-hook");
    const hookDest = path.join(getOpenClawDir(), "hooks", "clawrecord-hook");

    try {
      fs.mkdirSync(path.dirname(hookDest), { recursive: true });
      copyDirSync(hookSrc, hookDest);
      resolve({ success: true, path: hookDest });
    } catch (err) {
      reject(err);
    }
  });
}

function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function setupIpcHandlers() {
  ipcMain.handle("check-openclaw", async () => {
    const status = checkOpenClawInstalled();
    const binary = detectOpenClawBinary();
    const python = findPython();
    return { ...status, binary, pythonAvailable: !!python };
  });

  ipcMain.handle("install-openclaw", async () => {
    try {
      const result = await installOpenClaw();
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle("install-hook", async () => {
    try {
      const result = await installHook();
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle("refresh-data", async () => {
    try {
      await runPythonScript("collect.py");
      await runPythonScript("score.py");
      await runPythonScript("generate_pages.py");
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle("run-script", async (_event, scriptName) => {
    try {
      const result = await runPythonScript(scriptName);
      return { success: true, ...result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle("get-app-info", () => {
    return {
      version: app.getVersion(),
      platform: process.platform,
      arch: process.arch,
      electronVersion: process.versions.electron,
      nodeVersion: process.versions.node,
      openClawDir: getOpenClawDir(),
      resourcePath: app.isPackaged ? process.resourcesPath : path.join(__dirname, ".."),
    };
  });

  ipcMain.handle("open-external", async (_event, url) => {
    await shell.openExternal(url);
  });

  ipcMain.handle("open-path", async (_event, targetPath) => {
    await shell.openPath(targetPath);
  });

  ipcMain.handle("check-data-exists", () => {
    const dataJsPath = path.join(__dirname, "..", "docs", "data.js");
    return fs.existsSync(dataJsPath);
  });

  ipcMain.handle("setup-openclaw", async () => {
    const steps = [];
    try {
      const status = checkOpenClawInstalled();
      const binary = detectOpenClawBinary();

      if (!binary) {
        steps.push({ step: "install-openclaw", status: "running" });
        mainWindow?.webContents.send("setup-step", {
          step: "install-openclaw",
          status: "running",
        });
        try {
          await installOpenClaw();
          steps.push({ step: "install-openclaw", status: "done" });
          mainWindow?.webContents.send("setup-step", {
            step: "install-openclaw",
            status: "done",
          });
        } catch (err) {
          steps.push({
            step: "install-openclaw",
            status: "error",
            error: err.message,
          });
          mainWindow?.webContents.send("setup-step", {
            step: "install-openclaw",
            status: "error",
            error: err.message,
          });
        }
      } else {
        steps.push({ step: "install-openclaw", status: "skipped" });
        mainWindow?.webContents.send("setup-step", {
          step: "install-openclaw",
          status: "skipped",
          message: "OpenClaw already installed",
        });
      }

      const hookDir = path.join(getOpenClawDir(), "hooks", "clawrecord-hook");
      if (!fs.existsSync(hookDir)) {
        steps.push({ step: "install-hook", status: "running" });
        mainWindow?.webContents.send("setup-step", {
          step: "install-hook",
          status: "running",
        });
        try {
          await installHook();
          steps.push({ step: "install-hook", status: "done" });
          mainWindow?.webContents.send("setup-step", {
            step: "install-hook",
            status: "done",
          });
        } catch (err) {
          steps.push({
            step: "install-hook",
            status: "error",
            error: err.message,
          });
        }
      } else {
        steps.push({ step: "install-hook", status: "skipped" });
        mainWindow?.webContents.send("setup-step", {
          step: "install-hook",
          status: "skipped",
          message: "Hook already installed",
        });
      }

      return { success: true, steps };
    } catch (err) {
      return { success: false, error: err.message, steps };
    }
  });
}

// ── App Lifecycle ───────────────────────────────────────────────

app.whenReady().then(() => {
  setupIpcHandlers();
  buildAppMenu();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
