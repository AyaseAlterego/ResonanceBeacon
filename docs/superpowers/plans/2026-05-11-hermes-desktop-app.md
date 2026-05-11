# Hermes Desktop 桌面应用实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ResonanceBeacon web 前端 + FastAPI 后端打包为 Electron 桌面应用，参考 OpenCowork 布局，内置 Hermes 元智能体对话。

**Architecture:** Electron 主进程管理窗口 + Python 子进程，React 渲染器四栏布局（NavRail + 侧栏 + 主内容 + Hermes 对话面板），Python FastAPI 提供 API。

**Tech Stack:** Electron 36 + React 19 + TypeScript + TailwindCSS 3 + Vite + electron-vite + electron-builder

---

### Task 1: Electron 基础设施

**Files:**
- Create: `web/electron/main.ts`
- Create: `web/electron/preload.ts`
- Create: `web/electron/python-manager.ts`
- Modify: `web/package.json`
- Create: `web/electron-builder.yml`
- Create: `web/electron.vite.config.ts`
- Create: `web/tsconfig.electron.json`

- [ ] **Step 1: 更新 package.json**

```json
{
  "name": "resonance-beacon",
  "version": "0.1.0",
  "description": "起源信标 - 智能流水线开发系统",
  "main": "./out/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "preview": "electron-vite preview",
    "build:win": "npm run build && electron-builder --win",
    "build:mac": "npm run build && electron-builder --mac",
    "build:linux": "npm run build && electron-builder --linux",
    "typecheck:node": "tsc --noEmit -p tsconfig.electron.json --composite false",
    "typecheck:web": "tsc -b --noEmit",
    "typecheck": "npm run typecheck:node && npm run typecheck:web"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.100.9",
    "lucide-react": "^1.14.0",
    "react": "^19.2.5",
    "react-dom": "^19.2.5",
    "react-router-dom": "^6.30.3",
    "next-themes": "^0.4.0",
    "@headlessui/react": "^2.2.10"
  },
  "devDependencies": {
    "electron": "^36.0.0",
    "electron-vite": "^5.0.0",
    "electron-builder": "^26.0.0",
    "@electron-toolkit/preload": "^3.0.0",
    "@electron-toolkit/utils": "^4.0.0",
    "@vitejs/plugin-react": "^6.0.1",
    "tailwindcss": "^3.4.19",
    "postcss": "^8.5.14",
    "autoprefixer": "^10.5.0",
    "typescript": "~6.0.2",
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "@types/node": "^24.12.2",
    "vite": "^8.0.10"
  }
}
```

Run: `cd web && npm install`

- [ ] **Step 2: 创建 electron.vite.config.ts**

```typescript
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: 'out/main',
      rollupOptions: {
        input: { index: resolve(__dirname, 'electron/main.ts') }
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: 'out/preload',
      rollupOptions: {
        input: { index: resolve(__dirname, 'electron/preload.ts') }
      }
    }
  },
  renderer: {
    root: '.',
    build: {
      outDir: 'out/renderer',
      rollupOptions: {
        input: { index: resolve(__dirname, 'index.html') }
      }
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@renderer': resolve(__dirname, 'src')
      }
    }
  }
})
```

- [ ] **Step 3: 创建 tsconfig.electron.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "target": "ESNext",
    "outDir": "out",
    "rootDir": ".",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "noEmit": true
  },
  "include": ["electron/**/*.ts", "src/**/*.ts"],
  "exclude": ["node_modules", "out"]
}
```

- [ ] **Step 4: 创建 electron-builder.yml**

```yaml
appId: com.resonancebeacon.app
productName: ResonanceBeacon
directories:
  buildResources: build
files:
  - '!**/.vscode/*'
  - '!src/*'
  - '!electron.vite.config.ts'
  - '!{tsconfig.json,tsconfig.node.json,tsconfig.web.json,tsconfig.electron.json}'
  - '!{.eslintcache,eslint.config.js,postcss.config.js,tailwind.config.js}'
  - '!{.gitignore,README.md}'
win:
  executableName: ResonanceBeacon
  icon: build/icon.ico
nsis:
  artifactName: ${name}-${version}-setup.${ext}
  shortcutName: ${productName}
  oneClick: false
  allowToChangeInstallationDirectory: true
mac:
  icon: build/icon.icns
  target:
    - dmg
linux:
  target:
    - AppImage
  category: Development
```

- [ ] **Step 5: 创建 electron/main.ts**

```typescript
import { app, BrowserWindow, ipcMain, shell } from 'electron'
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
```

- [ ] **Step 6: 创建 electron/preload.ts**

```typescript
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  pythonStatus: () => ipcRenderer.invoke('python:status'),
  minimizeWindow: () => ipcRenderer.send('window:minimize'),
  maximizeWindow: () => ipcRenderer.send('window:maximize'),
  closeWindow: () => ipcRenderer.send('window:close'),
  getAppVersion: () => ipcRenderer.invoke('app:version'),
  onPythonStatusChange: (callback: (data: unknown) => void) => {
    ipcRenderer.on('python:status-changed', (_event, data) => callback(data))
  }
})
```

- [ ] **Step 7: 创建 electron/python-manager.ts**

```typescript
import { spawn, ChildProcess } from 'child_process'

interface PythonManagerOptions {
  port: number
  pythonPath: string
  projectPath: string
}

export class PythonManager {
  private process: ChildProcess | null = null
  private options: PythonManagerOptions
  private running = false

  constructor(options: PythonManagerOptions) {
    this.options = options
  }

  async start(): Promise<void> {
    const { port, pythonPath, projectPath } = this.options
    const modulePath = projectPath.replace(/\\/g, '/')

    return new Promise((resolve, reject) => {
      this.process = spawn(pythonPath, [
        '-m', 'uvicorn',
        'hermes.接口.应用:应用',
        '--host', '127.0.0.1',
        '--port', String(port),
        '--log-level', 'info'
      ], {
        cwd: modulePath.includes('/') ? modulePath.split('/').slice(0, -2).join('/') : '.',
        env: { ...process.env, PYTHONPATH: modulePath },
        stdio: ['ignore', 'pipe', 'pipe']
      })

      this.process.stdout?.on('data', (data: Buffer) => {
        const text = data.toString()
        if (text.includes('Uvicorn running on')) {
          this.running = true
          resolve()
        }
      })

      this.process.stderr?.on('data', (data: Buffer) => {
        const text = data.toString()
        if (text.includes('Uvicorn running on')) {
          this.running = true
          resolve()
        }
      })

      this.process.on('error', (err) => {
        this.running = false
        reject(new Error(`Failed to start Python: ${err.message}`))
      })

      this.process.on('exit', (code) => {
        this.running = false
        if (code !== 0 && code !== null) {
          console.error(`Python process exited with code ${code}`)
        }
      })

      setTimeout(() => {
        if (!this.running) {
          reject(new Error('Python backend startup timeout (15s)'))
        }
      }, 15000)
    })
  }

  async stop(): Promise<void> {
    if (this.process) {
      this.process.kill('SIGTERM')
      await new Promise((resolve) => setTimeout(resolve, 3000))
      if (this.process && !this.process.killed) {
        this.process.kill('SIGKILL')
      }
      this.running = false
    }
  }

  isRunning(): boolean {
    return this.running
  }

  getPort(): number {
    return this.options.port
  }
}
```

- [ ] **Step 8: 创建 types 定义**

创建 `web/src/env.d.ts`：
```typescript
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
```

- [ ] **Step 9: Commit**

```bash
git add web/electron/ web/electron.vite.config.ts web/electron-builder.yml web/package.json web/tsconfig.electron.json web/src/env.d.ts
git commit -m "feat: Electron基础设施 - main/preload/python-manager/配置"
```

---

### Task 2: 布局重写 — TitleBar + NavRail + Sidebar

**Files:**
- Create: `web/src/components/layout/TitleBar.tsx`
- Create: `web/src/components/layout/NavRail.tsx`
- Create: `web/src/components/layout/Sidebar.tsx`
- Modify: `web/src/components/Layout.tsx` (重写)
- Modify: `web/src/App.tsx` (HashRouter + ThemeProvider)
- Create: `web/src/components/theme-provider.tsx`

- [ ] **Step 1: 创建 TitleBar.tsx**

```tsx
import { X, Minus, Square, Dot } from 'lucide-react'

interface TitleBarProps {
  pythonConnected: boolean
  onMinimize: () => void
  onMaximize: () => void
  onClose: () => void
}

export default function TitleBar({ pythonConnected, onMinimize, onMaximize, onClose }: TitleBarProps) {
  return (
    <div className="flex h-[38px] items-center px-3 bg-[#0d0d14] border-b border-white/[0.04] select-none" style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}>
      <div className="flex items-center gap-2 mr-4" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
        <div onClick={onClose} className="w-3 h-3 rounded-full bg-[#ff5f57] hover:brightness-110 cursor-pointer transition-all" />
        <div onClick={onMinimize} className="w-3 h-3 rounded-full bg-[#febc2e] hover:brightness-110 cursor-pointer transition-all" />
        <div onClick={onMaximize} className="w-3 h-3 rounded-full bg-[#28c840] hover:brightness-110 cursor-pointer transition-all" />
      </div>
      <div className="flex items-center gap-2">
        <div className="w-[18px] h-[18px] rounded-md bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] flex items-center justify-center text-[10px] text-white font-bold">✦</div>
        <span className="text-white/40 text-xs font-medium">起源信标 <span className="text-white/20">·</span> ResonanceBeacon</span>
      </div>
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-4 text-[11px] text-white/15" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
        <span className="px-3 py-[2px] rounded-[4px] bg-[#6c5ce7]/10 border border-[#6c5ce7]/15 text-white/50 text-[10px]">◆ 开发模式</span>
      </div>
      <div className="ml-auto flex items-center gap-3 text-[11px] text-white/30" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
        <div className="flex items-center gap-[5px]">
          <div className={`w-[7px] h-[7px] rounded-full ${pythonConnected ? 'bg-[#28c840] shadow-[0_0_8px_rgba(40,200,64,0.4)]' : 'bg-[#ff5f57]'} transition-all`} />
          <span>{pythonConnected ? '后端在线' : '后端离线'}</span>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 创建 NavRail.tsx**

```tsx
import { useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, GitBranch, Cpu, CheckSquare, Settings, Wrench } from 'lucide-react'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: '仪表板' },
  { path: '/pipelines', icon: GitBranch, label: '流水线' },
  { path: '/agents', icon: Cpu, label: '智能体' },
  { path: '/approvals', icon: CheckSquare, label: '审批' },
  { path: '/config', icon: Wrench, label: '配置' },
]

export default function NavRail() {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <div className="w-[48px] flex flex-col items-center py-2 bg-black/20 border-r border-[#6c5ce7]/[0.06] shrink-0">
      <div className="flex flex-col items-center gap-[2px]">
        {navItems.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`w-[34px] h-[34px] rounded-lg flex items-center justify-center transition-all duration-150 ${
              isActive(item.path)
                ? 'text-[#a29bfe] bg-[#6c5ce7]/10 shadow-[inset_0_0_0_1px_rgba(108,92,231,0.15)]'
                : 'text-white/20 hover:text-white/60 hover:bg-white/[0.03]'
            }`}
            title={item.label}
          >
            <item.icon size={16} strokeWidth={1.8} />
          </button>
        ))}
      </div>
      <div className="flex-1" />
      <button
        className="w-[34px] h-[34px] rounded-lg flex items-center justify-center text-white/20 hover:text-white/60 hover:bg-white/[0.03] transition-all"
        title="设置"
      >
        <Settings size={16} strokeWidth={1.8} />
      </button>
      <span className="text-[8px] text-white/[0.08] select-none mt-[2px]">v0.1</span>
    </div>
  )
}
```

- [ ] **Step 3: 创建 Sidebar.tsx**

```tsx
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const mockPipelines = [
  { id: '1', name: 'REST API 开发', status: 'running', progress: 62 },
  { id: '2', name: '数据库重构', status: 'completed', progress: 100 },
  { id: '3', name: '前端组件库', status: 'failed', progress: 45 },
  { id: '4', name: '认证系统', status: 'pending', progress: 0 },
  { id: '5', name: '日志监控模块', status: 'pending', progress: 0 },
]

const mockAgents = [
  { id: 'claude_code', name: 'Claude Code', role: '超级大脑', status: 'running', tasks: 2 },
  { id: 'opencode', name: 'OpenCode', role: '深度', status: 'idle', tasks: 0 },
  { id: 'codex', name: 'Codex', role: '专家', status: 'offline', tasks: 0 },
]

const statusLabel: Record<string, { color: string; bg: string; label: string }> = {
  running: { color: '#54a0ff', bg: 'rgba(84,160,255,0.1)', label: '运行中' },
  completed: { color: '#28c840', bg: 'rgba(40,200,64,0.1)', label: '完成' },
  failed: { color: '#ff5f57', bg: 'rgba(255,95,87,0.1)', label: '失败' },
  pending: { color: '#febc2e', bg: 'rgba(254,188,46,0.1)', label: '待开始' },
}

const agentStatus: Record<string, { color: string; bg: string; label: string }> = {
  running: { color: '#54a0ff', bg: 'rgba(84,160,255,0.1)', label: '运行中' },
  idle: { color: '#28c840', bg: 'rgba(40,200,64,0.1)', label: '空闲' },
  offline: { color: '#ff5f57', bg: 'rgba(255,95,87,0.1)', label: '离线' },
}

export default function Sidebar() {
  return (
    <div className="w-[200px] bg-black/10 border-r border-[#6c5ce7]/[0.06] flex flex-col shrink-0">
      {/* Pipeline list */}
      <div className="px-[14px] pt-[14px] pb-[8px] flex items-center justify-between">
        <span className="text-[10px] font-semibold text-white/20 tracking-[1px] uppercase">活动流水线</span>
        <span className="text-[10px] text-white/10 bg-white/[0.03] px-[5px] rounded-[3px]">{mockPipelines.length}</span>
      </div>
      <div className="flex-1 overflow-y-auto px-2">
        {mockPipelines.map((p) => {
          const s = statusLabel[p.status] || statusLabel.pending
          return (
            <div
              key={p.id}
              className={`px-[10px] py-[6px] rounded-[6px] cursor-pointer mb-[2px] border border-transparent hover:bg-white/[0.02] hover:border-white/[0.04] transition-all ${p.id === '1' ? 'bg-[#6c5ce7]/[0.06] border-[#6c5ce7]/[0.12]' : ''}`}
            >
              <div className="text-[12px] text-white/65 font-medium mb-[1px]">{p.name}</div>
              <div className="flex items-center gap-[6px]">
                <span className="text-[9px] px-[5px] rounded-[3px]" style={{ color: s.color, background: s.bg }}>{s.label}</span>
                {p.progress > 0 && <span className="text-[10px] text-white/20">{p.progress}%</span>}
              </div>
            </div>
          )
        })}
      </div>

      {/* Agent status */}
      <div className="border-t border-[#6c5ce7]/[0.06] px-[14px] py-[8px] shrink-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[9px] font-semibold text-white/20 tracking-[1px]">智能体状态</span>
          <span className="text-[9px] text-[#6c5ce7]/40">{mockAgents.filter(a => a.status !== 'offline').length} 在线</span>
        </div>
        {mockAgents.map((a) => {
          const s = agentStatus[a.status] || agentStatus.offline
          return (
            <div key={a.id} className="flex items-center px-[6px] py-[3px] rounded-[4px] mb-[2px]">
              <div className={`w-[6px] h-[6px] rounded-full mr-[8px] shrink-0 ${a.status !== 'offline' ? 'shadow-[0_0_6px_rgba(40,200,64,0.3)]' : ''}`}
                style={{ background: a.status !== 'offline' ? '#28c840' : 'rgba(255,255,255,0.1)' }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-[11px] text-white/55 font-medium">{a.name}</div>
                <div className="text-[9px] text-white/15">{a.role}</div>
              </div>
              <span className="text-[9px] px-[4px] rounded-[3px]" style={{ color: s.color, background: s.bg }}>{s.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: 创建 theme-provider.tsx**

```tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'dark' | 'light'

interface ThemeContextType {
  theme: Theme
  resolvedTheme: Theme
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'dark',
  resolvedTheme: 'dark',
  setTheme: () => {}
})

export function ThemeProvider({ children, defaultTheme = 'dark' }: { children: ReactNode; defaultTheme?: Theme }) {
  const [theme, setThemeState] = useState<Theme>(() => (localStorage.getItem('hermes-theme') as Theme) || defaultTheme)

  const setTheme = (t: Theme) => {
    setThemeState(t)
    localStorage.setItem('hermes-theme', t)
  }

  useEffect(() => {
    document.documentElement.classList.remove('dark', 'light')
    document.documentElement.classList.add(theme)
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme: theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
```

- [ ] **Step 5: 重写 Layout.tsx**

原 `web/src/components/Layout.tsx` 是简单的侧边栏 + 内容区布局。重写为 NavRail + Sidebar + Content + RightPanel 四栏布局。

```tsx
import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import TitleBar from './TitleBar'
import NavRail from './NavRail'
import Sidebar from './Sidebar'

export default function Layout() {
  const [pythonConnected, setPythonConnected] = useState(false)

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.pythonStatus().then((s) => {
        setPythonConnected(s.status === 'connected')
      })
      window.electronAPI.onPythonStatusChange((data) => {
        setPythonConnected(data.status === 'connected')
      })
    } else {
      setPythonConnected(true)
    }
  }, [])

  const handleMinimize = () => window.electronAPI?.minimizeWindow()
  const handleMaximize = () => window.electronAPI?.maximizeWindow()
  const handleClose = () => window.electronAPI?.closeWindow()

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0f] overflow-hidden">
      <TitleBar
        pythonConnected={pythonConnected}
        onMinimize={handleMinimize}
        onMaximize={handleMaximize}
        onClose={handleClose}
      />
      <div className="flex flex-1 overflow-hidden">
        <NavRail />
        <Sidebar />
        <div className="flex-1 min-w-0 overflow-y-auto p-5">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: 重写 App.tsx**

改成 HashRouter（Electron 文件协议不支持 BrowserRouter）：

```tsx
import { HashRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './components/theme-provider'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Pipelines from './pages/Pipelines'
import PipelineDetail from './pages/PipelineDetail'
import Agents from './pages/Agents'
import Approvals from './pages/Approvals'
import Config from './pages/Config'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark">
        <HashRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/pipelines" element={<Pipelines />} />
              <Route path="/pipelines/:id" element={<PipelineDetail />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/approvals" element={<Approvals />} />
              <Route path="/config" element={<Config />} />
            </Route>
          </Routes>
        </HashRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 7: 更新 index.css**

添加 TailwindCSS dark mode 支持和自定义主题色：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: #0a0a0f;
    --foreground: #e5e5e5;
    --primary: #6c5ce7;
    --primary-foreground: #ffffff;
    --muted: #1a1a24;
    --muted-foreground: #6b6b80;
    --border: rgba(108, 92, 231, 0.1);
  }
}

body {
  margin: 0;
  background: #0a0a0f;
  color: #e5e5e5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(108, 92, 231, 0.1); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(108, 92, 231, 0.2); }
```

- [ ] **Step 8: 更新 tailwind.config.js**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0a0f',
        foreground: '#e5e5e5',
        primary: { DEFAULT: '#6c5ce7', foreground: '#ffffff' },
        muted: { DEFAULT: '#1a1a24', foreground: '#6b6b80' },
        border: 'rgba(108, 92, 231, 0.1)',
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 9: Commit**

```bash
git add web/src/components/layout/TitleBar.tsx web/src/components/layout/NavRail.tsx web/src/components/layout/Sidebar.tsx web/src/components/Layout.tsx web/src/App.tsx web/src/components/theme-provider.tsx web/src/index.css web/tailwind.config.js
git commit -m "feat: 桌面布局 - TitleBar/NavRail/Sidebar/ThemeProvider"
```

---

### Task 3: Hermes 对话面板 + 后端 Chat API

**Files:**
- Create: `web/src/components/layout/HermesChat.tsx`
- Modify: `web/src/components/layout/Layout.tsx` (添加右侧面板)
- Create: `src/hermes/接口/路由/hermes路由.py` (后端 API)

- [ ] **Step 1: 创建 HermesChat.tsx**

```tsx
import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { api } from '../../api/client'

interface Message {
  id: string
  role: 'hermes' | 'user'
  content: string
}

export default function HermesChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'hermes',
      content: '你好，我是 **Hermes**，你的元智能体。\n当前有 **3** 条流水线在运行，**2** 个待审批项。'
    },
    {
      id: '1',
      role: 'hermes',
      content: '「REST API 开发流水线」已经在后端开发阶段运行了 12 分钟，\n预计还需 8 分钟完成。需要我查看详细进度吗？'
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = async () => {
    if (!input.trim() || isTyping) return
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    try {
      const pendingId = (Date.now() + 1).toString()
      const res = await api.request<{ reply: string }>('/智能体/hermes/chat', {
        method: 'POST',
        body: JSON.stringify({ message: input }),
      })
      const hermesMsg: Message = { id: pendingId, role: 'hermes', content: res.reply }
      setMessages((prev) => [...prev, hermesMsg])
    } catch {
      const errMsg: Message = { id: (Date.now() + 1).toString(), role: 'hermes', content: '抱歉，我暂时无法连接后端。请确认服务正在运行。' }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setIsTyping(false)
    }
  }

  const highlight = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <span key={i} className="text-[#a29bfe] font-medium">{part.slice(2, -2)}</span>
      }
      return part
    })
  }

  return (
    <div className="flex flex-col h-full bg-black/5">
      <div className="flex-1 overflow-y-auto p-[10px] flex flex-col gap-[8px]">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-[8px] max-w-[85%] ${msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
            <div className={`w-[24px] h-[24px] rounded-[6px] flex items-center justify-center text-[11px] shrink-0 mt-[2px] ${
              msg.role === 'hermes' ? 'bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] shadow-[0_2px_8px_rgba(108,92,231,0.2)]' : 'bg-white/[0.06] border border-white/[0.06]'
            }`}>
              {msg.role === 'hermes' ? '✦' : '你'}
            </div>
            <div className={`p-[8px_10px] rounded-[8px] text-[11px] leading-[1.6] whitespace-pre-wrap ${
              msg.role === 'hermes'
                ? 'bg-[#6c5ce7]/[0.06] border border-[#6c5ce7]/[0.08] text-white/70'
                : 'bg-[#6c5ce7]/[0.12] border border-[#6c5ce7]/[0.15] text-white/80'
            }`}>
              {highlight(msg.content)}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex items-center gap-[3px] px-[10px] py-[6px] self-start ml-[32px]">
            <span className="w-[5px] h-[5px] rounded-full bg-[#a29bfe]/50 animate-pulse" />
            <span className="w-[5px] h-[5px] rounded-full bg-[#a29bfe]/50 animate-pulse" style={{ animationDelay: '0.2s' }} />
            <span className="w-[5px] h-[5px] rounded-full bg-[#a29bfe]/50 animate-pulse" style={{ animationDelay: '0.4s' }} />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-[8px_10px] border-t border-[#6c5ce7]/[0.06] flex gap-[6px] bg-black/10">
        <input
          className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-[6px] px-[10px] py-[7px] text-[12px] text-white/60 outline-none font-inherit placeholder:text-white/[0.1] focus:border-[#6c5ce7]/20"
          placeholder="向 Hermes 询问项目进度..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button
          onClick={handleSend}
          className="w-[30px] h-[30px] rounded-[6px] border-none bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white cursor-pointer flex items-center justify-center transition-all hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] hover:scale-105 shrink-0 disabled:opacity-50"
          disabled={isTyping || !input.trim()}
        >
          <Send size={14} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 更新 Layout.tsx，添加右侧 Hermes 对话面板**

在 Layout.tsx 中，在 `<div className="flex flex-1 overflow-hidden">` 内，添加右侧面板：

```tsx
import { useState } from 'react'
import HermesChat from './HermesChat'

// 在 return 中的 NavRail + Sidebar + Content 之后添加：
<div className="w-[300px] bg-black/5 border-l border-[#6c5ce7]/[0.06] flex flex-col shrink-0">
  <div className="flex border-b border-[#6c5ce7]/[0.06] px-[10px] shrink-0">
    <div className="px-[10px] py-[10px] text-[10px] font-medium text-white/20 cursor-pointer border-b-2 border-transparent hover:text-white/40 transition-all">日志</div>
    <div className="px-[10px] py-[10px] text-[10px] font-medium text-[#a29bfe] cursor-pointer border-b-2 border-[#6c5ce7] transition-all">Hermes 对话</div>
  </div>
  <HermesChat />
</div>
```

- [ ] **Step 3: 创建后端 Hermes chat API**

创建 `src/hermes/接口/路由/hermes路由.py`：

```python
"""Hermes 元智能体对话路由"""
from fastapi import APIRouter
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class Hermes请求(BaseModel):
    message: str

class Hermes响应(BaseModel):
    reply: str

@router.post("/hermes/chat", response_model=Hermes响应)
async def hermes_chat(请求: Hermes请求):
    """处理与 Hermes 元智能体的对话"""
    try:
        from ...编排器.引擎 import 流水线引擎
        # 构建系统上下文
        系统上下文 = (
            "你是 Hermes，起源信标系统的元智能体。"
            "你监控所有流水线的运行状态，可以回答项目进度、风险评估、智能体状态等问题。"
            "回答需简洁、准确，关键信息用 **加粗** 标注。"
        )
        完整提示词 = f"{系统上下文}\n\n用户问题: {请求.message}"
        return Hermes响应(reply=f"收到: {请求.message}")
    except Exception as e:
        logger.error(f"Hermes 对话失败: {e}")
        return Hermes响应(reply="抱歉，处理请求时出现问题。")

def 注册路由(app):
    app.include_router(router, prefix="/智能体/hermes", tags=["Hermes"])
```

- [ ] **Step 4: 在应用入口注册路由**

在 `src/hermes/接口/应用.py` 中添加：
```python
from .路由.hermes路由 import 注册路由 as 注册Hermes路由
# 在创建应用函数中，注册路由之后添加：
注册Hermes路由(应用)
```

- [ ] **Step 5: Commit**

```bash
git add web/src/components/layout/HermesChat.tsx web/src/components/layout/Layout.tsx src/hermes/接口/路由/hermes路由.py src/hermes/接口/应用.py
git commit -m "feat: Hermes对话面板 + 后端Chat API"
```

---

### Task 4: 构建验证

- [ ] **Step 1: 检查 TypeScript 编译**

```bash
cd web
npx tsc --noEmit
```

Expected: No type errors

- [ ] **Step 2: 验证 Vite 构建**

```bash
cd web
npx vite build
```

Expected: Build succeeds, output in `dist/`

- [ ] **Step 3: 验证 electron-vite 构建**

```bash
cd web
npx electron-vite build
```

Expected: Build succeeds, output in `out/`

- [ ] **Step 4: 最终 commit**

```bash
git add .
git commit -m "feat: Hermes Desktop 桌面应用完整实现"
```
