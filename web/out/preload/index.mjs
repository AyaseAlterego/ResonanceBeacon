import { contextBridge, ipcRenderer } from "electron";
//#region electron/preload.ts
contextBridge.exposeInMainWorld("electronAPI", {
	pythonStatus: () => ipcRenderer.invoke("python:status"),
	minimizeWindow: () => ipcRenderer.send("window:minimize"),
	maximizeWindow: () => ipcRenderer.send("window:maximize"),
	closeWindow: () => ipcRenderer.send("window:close"),
	getAppVersion: () => ipcRenderer.invoke("app:version"),
	onPythonStatusChange: (callback) => {
		const handler = (_event, data) => callback(data);
		ipcRenderer.on("python:status-changed", handler);
		return () => ipcRenderer.removeListener("python:status-changed", handler);
	}
});
//#endregion
export {};
