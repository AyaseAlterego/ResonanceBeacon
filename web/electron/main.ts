import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { PythonManager } from './python-manager'

let mainWindow: BrowserWindow | null = null
let pythonManager: PythonManager | null = null

const isDev = !app.isPackaged

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1300,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    show: false,
    backgroundColor: '#0a0a0f',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

async function startPythonBackend(): Promise<void> {
  pythonManager = new PythonManager({
    port: 8765,
    pythonPath: process.env.HERMES_PYTHON_PATH || 'python',
    projectPath: app.isPackaged
      ? join(process.resourcesPath, 'backend')
      : join(__dirname, '..', '..', '..', 'src')
  })

  try {
    await pythonManager.start()
    mainWindow?.webContents.send('python:status-changed', { status: 'connected' })
  } catch (err) {
    mainWindow?.webContents.send('python:status-changed', {
      status: 'error',
      error: String(err)
    })
  }
}

app.whenReady().then(async () => {
  createWindow()

  ipcMain.handle('python:status', () => {
    return {
      status: pythonManager?.isRunning() ? 'connected' : 'disconnected',
      port: pythonManager?.getPort() ?? 8765
    }
  })

  ipcMain.handle('app:version', () => {
    return app.getVersion()
  })

  ipcMain.on('window:minimize', () => {
    mainWindow?.minimize()
  })

  ipcMain.on('window:maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow?.maximize()
    }
  })

  ipcMain.on('window:close', () => {
    mainWindow?.close()
  })

  await startPythonBackend()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', async () => {
  if (pythonManager) {
    await pythonManager.stop()
  }
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
