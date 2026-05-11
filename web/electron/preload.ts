import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  pythonStatus: () => ipcRenderer.invoke('python:status'),
  minimizeWindow: () => ipcRenderer.send('window:minimize'),
  maximizeWindow: () => ipcRenderer.send('window:maximize'),
  closeWindow: () => ipcRenderer.send('window:close'),
  getAppVersion: () => ipcRenderer.invoke('app:version'),
  onPythonStatusChange: (callback: (data: { status: string; error?: string }) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, data: unknown) => callback(data as { status: string; error?: string })
    ipcRenderer.on('python:status-changed', handler)
    return () => ipcRenderer.removeListener('python:status-changed', handler)
  }
})
