const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("clawrecord", {
  checkOpenClaw: () => ipcRenderer.invoke("check-openclaw"),
  installOpenClaw: () => ipcRenderer.invoke("install-openclaw"),
  installHook: () => ipcRenderer.invoke("install-hook"),
  setupOpenClaw: () => ipcRenderer.invoke("setup-openclaw"),
  refreshData: () => ipcRenderer.invoke("refresh-data"),
  runScript: (name) => ipcRenderer.invoke("run-script", name),
  getAppInfo: () => ipcRenderer.invoke("get-app-info"),
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
  openPath: (p) => ipcRenderer.invoke("open-path", p),
  checkDataExists: () => ipcRenderer.invoke("check-data-exists"),

  onInstallProgress: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on("install-progress", handler);
    return () => ipcRenderer.removeListener("install-progress", handler);
  },

  onSetupStep: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on("setup-step", handler);
    return () => ipcRenderer.removeListener("setup-step", handler);
  },

  onTriggerRefresh: (callback) => {
    const handler = () => callback();
    ipcRenderer.on("trigger-refresh", handler);
    return () => ipcRenderer.removeListener("trigger-refresh", handler);
  },
});
