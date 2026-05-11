/// <reference types="vite/client" />

interface ElectronAPI {
  pythonStatus: () => Promise<{ status: string; port: number }>
  minimizeWindow: () => void
  maximizeWindow: () => void
  closeWindow: () => void
  getAppVersion: () => Promise<string>
  onPythonStatusChange: (callback: (data: { status: string; error?: string }) => void) => void
}

interface Window {
  electronAPI?: ElectronAPI
}
