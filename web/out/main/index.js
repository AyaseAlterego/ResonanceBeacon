import { BrowserWindow, app, ipcMain } from "electron";
import { join } from "path";
import { spawn } from "child_process";
// -- CommonJS Shims --
import __cjs_mod__ from "node:module";
import.meta.filename;
const __dirname = import.meta.dirname;
__cjs_mod__.createRequire(import.meta.url);
//#region electron/python-manager.ts
var PythonManager = class {
	constructor(options) {
		this.process = null;
		this.running = false;
		this.options = options;
	}
	async start() {
		const { port, pythonPath, projectPath } = this.options;
		const modulePath = projectPath.replace(/\\/g, "/");
		return new Promise((resolve, reject) => {
			let resolved = false;
			this.process = spawn(pythonPath, [
				"-m",
				"uvicorn",
				"hermes.接口.应用:应用",
				"--host",
				"127.0.0.1",
				"--port",
				String(port),
				"--log-level",
				"info"
			], {
				cwd: modulePath,
				env: {
					...process.env,
					PYTHONPATH: modulePath
				},
				stdio: [
					"ignore",
					"pipe",
					"pipe"
				]
			});
			const onData = (data) => {
				if (!resolved && data.toString().includes("Uvicorn running on")) {
					resolved = true;
					this.running = true;
					resolve();
				}
			};
			this.process.stdout?.on("data", onData);
			this.process.stderr?.on("data", onData);
			this.process.on("error", (err) => {
				resolved = true;
				this.running = false;
				reject(/* @__PURE__ */ new Error(`Failed to start Python: ${err.message}`));
			});
			this.process.on("exit", (code) => {
				if (!resolved) {
					resolved = true;
					this.running = false;
					reject(/* @__PURE__ */ new Error(`Python process exited with code ${code ?? "unknown"} before starting`));
				}
			});
			const timeout = setTimeout(() => {
				if (!resolved) {
					resolved = true;
					reject(/* @__PURE__ */ new Error("Python backend startup timeout (15s)"));
				}
			}, 15e3);
			this.process.on("close", () => clearTimeout(timeout));
		});
	}
	async stop() {
		if (this.process) {
			this.process.kill("SIGTERM");
			await new Promise((resolve) => setTimeout(resolve, 3e3));
			if (this.process && !this.process.killed) this.process.kill("SIGKILL");
			this.running = false;
		}
	}
	isRunning() {
		return this.running;
	}
	getPort() {
		return this.options.port;
	}
};
//#endregion
//#region electron/main.ts
var mainWindow = null;
var pythonManager = null;
var isDev = !app.isPackaged;
function createWindow() {
	mainWindow = new BrowserWindow({
		width: 1300,
		height: 820,
		minWidth: 900,
		minHeight: 600,
		frame: false,
		show: false,
		backgroundColor: "#0a0a0f",
		webPreferences: {
			preload: join(__dirname, "../preload/index.js"),
			sandbox: false,
			contextIsolation: true,
			nodeIntegration: false
		}
	});
	mainWindow.on("ready-to-show", () => {
		mainWindow?.show();
	});
	if (isDev) mainWindow.loadURL("http://localhost:5173");
	else mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
}
async function startPythonBackend() {
	pythonManager = new PythonManager({
		port: 8765,
		pythonPath: process.env.HERMES_PYTHON_PATH || "python",
		projectPath: app.isPackaged ? join(process.resourcesPath, "backend") : join(__dirname, "..", "..", "..", "src")
	});
	try {
		await pythonManager.start();
		mainWindow?.webContents.send("python:status-changed", { status: "connected" });
	} catch (err) {
		mainWindow?.webContents.send("python:status-changed", {
			status: "error",
			error: String(err)
		});
	}
}
app.on("activate", () => {
	if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
app.whenReady().then(async () => {
	createWindow();
	ipcMain.handle("python:status", () => {
		return {
			status: pythonManager?.isRunning() ? "connected" : "disconnected",
			port: pythonManager?.getPort() ?? 8765
		};
	});
	ipcMain.handle("app:version", () => {
		return app.getVersion();
	});
	ipcMain.on("window:minimize", () => {
		mainWindow?.minimize();
	});
	ipcMain.on("window:maximize", () => {
		if (mainWindow?.isMaximized()) mainWindow.unmaximize();
		else mainWindow?.maximize();
	});
	ipcMain.on("window:close", () => {
		mainWindow?.close();
	});
	await startPythonBackend();
});
app.on("window-all-closed", async () => {
	if (pythonManager) await pythonManager.stop();
	if (process.platform !== "darwin") app.quit();
});
//#endregion
export {};
