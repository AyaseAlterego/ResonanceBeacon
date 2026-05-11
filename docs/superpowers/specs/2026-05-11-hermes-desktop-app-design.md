# 起源信标桌面应用设计文档

> **目标：** 将 ResonanceBeacon 现有的 web 前端 + Python FastAPI 后端打包为 Electron 桌面应用，参考 OpenCowork 的 NavRail 布局，内置 Hermes 元智能体对话功能。

**架构：** Electron 主进程管理窗口和 Python 子进程生命周期，React 渲染器展示 NavRail + 侧栏 + 主内容 + Hermes 对话面板四栏布局，Python FastAPI 后端通过 localhost HTTP 提供 API。

**技术栈：** Electron + Vite + React 19 + TypeScript + TailwindCSS 3 + electron-vite + electron-builder

---

## 1. 页面结构

### 1.1 整体布局

```
┌──────────────────────────────────────────────────────────────┐
│ TitleBar (frameless, traffic lights, 拖拽区域, 后端状态灯)   │
├──┬────────┬─────────────────────────────┬───────────────────┤
│N │ Sidebar│  Main Content                │ Right Panel       │
│a │  ├ 活动  │  (Dashboard / Pipelines /  │ (Hermes Chat)     │
│v │  流水线 │   Agents / Approvals /     │  ├ 日志            │
│R │  │      │   Config)                   │  ├ Hermes 对话     │
│a │  ├ 智能体│                             │  └ 设置           │
│i │  状态   │                             │                   │
│l │  │      │                             │                   │
└──┴────────┴─────────────────────────────┴───────────────────┘
```

### 1.2 页面列表

| 路由 | 页面 | 来源 |
|------|------|------|
| `#/` | 仪表板 — 运行总览、进度英雄区、统计卡片 | 现有 Dashboard.tsx |
| `#/pipelines` | 流水线列表 | 现有 Pipelines.tsx |
| `#/pipelines/:id` | 流水线详情 | 现有 PipelineDetail.tsx |
| `#/agents` | 智能体管理 | 现有 Agents.tsx |
| `#/approvals` | 审批管理 | 现有 Approvals.tsx |
| `#/config` | 配置管理 | 现有 Config.tsx |

### 1.3 新组件

| 组件 | 功能 | 参考来源 |
|------|------|---------|
| `electron/main.ts` | Electron 主进程，创建 frameless 窗口 | OpenCowork |
| `electron/preload.ts` | IPC bridge，暴露 Python 状态、窗口控制 | OpenCowork |
| `electron/python-manager.ts` | spawn uvicorn，health check，graceful shutdown | 新建 |
| `src/components/layout/TitleBar.tsx` | Frameless 标题栏，macOS traffic lights，拖拽区域 | OpenCowork NavRail |
| `src/components/layout/NavRail.tsx` | 左侧图标导航栏（仪表板/流水线/智能体/审批/配置/设置） | OpenCowork NavRail |
| `src/components/layout/Sidebar.tsx` | 左侧栏：活动流水线列表 + 智能体状态 | 新建 |
| `src/components/layout/HermesChat.tsx` | Hermes 元智能体对话面板，位于右侧 | 新建 |
| `src/components/PythonStatus.tsx` | 标题栏上的后端连接状态指示器 | 新建 |

---

## 2. Electron 架构

### 2.1 主进程 (`electron/main.ts`)

- 创建 frameless BrowserWindow (`frame: false`)
- 加载 `index.html` (开发: vite dev server, 生产: 本地文件)
- macOS 保留 traffic lights，Windows 自定义标题栏
- 管理 Python 后端生命周期（启动、健康检查、关闭）
- IPC handlers: `python:status`, `window:minimize`, `window:close`, `app:version`

### 2.2 Preload (`electron/preload.ts`)

通过 `contextBridge` 暴露：
```typescript
window.electronAPI = {
  pythonStatus: () => ipcRenderer.invoke('python:status'),
  minimizeWindow: () => ipcRenderer.send('window:minimize'),
  closeWindow: () => ipcRenderer.send('window:close'),
  getAppVersion: () => ipcRenderer.invoke('app:version'),
  onPythonStatusChange: (callback) => ipcRenderer.on('python:status-changed', callback),
  onHermesResponse: (callback) => ipcRenderer.on('hermes:response', callback),
  sendHermesMessage: (msg) => ipcRenderer.invoke('hermes:chat', msg),
}
```

### 2.3 Python 进程管理 (`electron/python-manager.ts`)

```
启动 → spawn uvicorn (--port 8765) → 轮询 /健康/健康 (超时 15s)
  → 成功: 通知渲染器 "connected"
  → 失败: 显示错误页面，提供重试按钮
关闭 → SIGTERM → wait 3s → SIGKILL
```

- 端口默认 8765，可通过 `--port` 参数指定
- 支持 `--python-path` 指定 Python 解释器路径
- Python 崩溃后自动重启（最多 3 次）

---

## 3. 渲染器布局组件

### 3.1 TitleBar

- 高度 38px
- 左侧: macOS traffic lights (红/黄/绿圆点)
- 中部: 品牌名 + 版本 + 后端状态灯
- 右侧: 窗口控制按钮 (Win: 最小化/最大化/关闭)
- `-webkit-app-region: drag` 实现拖拽

### 3.2 NavRail

- 宽度 48px
- 固定图标列表，每个 34x34px，hover 高亮
- 激活项紫色高亮 + 背景
- 底部: 设置齿轮 + 版本号

Nav 图标顺序: 仪表板 → 流水线 → 智能体 → 审批(有badge) → 配置 | spacer | 设置

### 3.3 Sidebar

- 宽度 200px
- 上半部: 活动流水线列表（名称 + 状态标签 + 进度百分比）
- 下半部: 智能体状态列表（名称 + 角色 + 状态标签）

### 3.4 主内容区

- 基于 hash 路由渲染对应页面
- 页面切换动画 (fade)
- 使用现有 web/ 中的所有 page 组件

### 3.5 Hermes 对话面板 (右侧)

- 宽度 300px
- 标签切换: 日志 / Hermes 对话 / (预留)
- Hermes 对话:
  - 消息列表: 气泡样式，Hermes 紫色，用户灰白色
  - 底部输入框 + 发送按钮
  - 输入框支持 Enter 发送
  - Hermes 消息中的关键数据高亮（数字、状态、风险）
  - 输入框上方显示 / 隐式上下文（当前页面、活跃流水线）

对话 API:
- 前端 POST `/智能体/hermes/chat` → 后端调用 Claude Code API 生成回答
- 返回流式 SSE，逐 token 渲染

---

## 4. 数据流

```
用户操作 → React Page → API Client (fetch)
  → localhost:8765 (Python FastAPI)
  → Hermes Engine → 智能体适配器
  → 响应 → API Client → React State → UI 更新

Hermes 对话:
  用户输入 → HermesChat组件 → API Client → POST /智能体/hermes/chat
    → 后端构建上下文(当前流水线状态/智能体状态/审批列表)
    → 调用 Claude Code API → SSE 流式返回
    → HermesChat 逐 token 渲染
```

---

## 5. 状态管理

- `@tanstack/react-query` — API 数据缓存（复用现有）
- 现有各 page 组件的本地状态保持不变
- 新增：
  - `usePythonStatus` — 后端连接状态 (Electron IPC)
  - `useHermesChat` — 对话消息 + 发送/接收

---

## 6. 构建和打包

### 6.1 构建方式

```bash
npm run dev          # 开发: electron-vite dev，同时启动 Python
npm run build:win    # 打包 Windows exe (NSIS 安装包)
npm run build:mac    # 打包 macOS dmg
npm run build:linux  # 打包 Linux AppImage
```

### 6.2 electron-builder 配置

- appId: `com.resonancebeacon.app`
- productName: `ResonanceBeacon`
- 目标: nsis (win), dmg (mac), AppImage (linux)
- 不打包 Python (要求系统已安装 Python 3.12+)

### 6.3 package.json 新增依赖

```json
{
  "devDependencies": {
    "electron": "^36.0.0",
    "electron-vite": "^5.0.0",
    "electron-builder": "^26.0.0",
    "@electron-toolkit/preload": "^3.0.0",
    "@electron-toolkit/utils": "^4.0.0"
  },
  "dependencies": {
    "next-themes": "^0.4.0",
    "react-router-dom": "^6.30.0"
  }
}
```

---

## 7. 原型确认

本设计基于已确认的 HTML 原型 v2，关键布局元素：
- [x] 深空科技感主题，紫色主色调 (#6c5ce7)
- [x] NavRail 左侧图标导航
- [x] 侧栏上方流水线列表 + 下方智能体状态
- [x] 进度英雄区（进度条 + 分步指示器 + 百分比）
- [x] Hermes 元智能体对话面板（右侧）
- [x] 统计卡片 + 最近运行列表
- [x] Frameless 标题栏 + 后端状态灯
