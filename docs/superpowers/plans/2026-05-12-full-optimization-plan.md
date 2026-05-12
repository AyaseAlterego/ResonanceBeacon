# 全面优化计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 ResonanceBeacon 从可运行的原型提升为可实际使用的开发者工具，填补所有 stub 实现，完善前端交互，强化质量。

**Current state:**
- ✅ 42/42 Python 单元测试通过
- ✅ 11/11 API 端点端到端验证通过
- ✅ Electron 桌面应用布局完整（NavRail + Sidebar + Content + HermesChat）
- ✅ 认证系统可用（本地开发密钥自动配置）
- ⚠️ 大量 API 端点为 stub（返回空数据或硬编码数据）
- ⚠️ 前端页面显示"暂无数据"空状态
- ⚠️ 核心流水线引擎未实际接入 API

---

### Phase 1: 后端功能实现（填补 Stub）

#### Task 1.1: 流水线 CRUD 内存存储

**Files:**
- Create: `src/hermes/接口/存储.py` — 内存存储层

当前所有路由（流水线/智能体/审批）返回硬编码空数据。创建统一的内存存储层：

```python
"""内存数据存储"""
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
from datetime import datetime

@dataclass
class 流水线记录:
    ID: str
    名称: str
    描述: str = ""
    状态: str = "pending"
    阶段数: int = 0
    完成阶段数: int = 0
    创建时间: str = ""

@dataclass
class 智能体记录:
    ID: str
    名称: str
    类别: str
    状态: str = "idle"
    负载: float = 0.0

@dataclass
class 审批记录:
    ID: str
    流水线ID: str
    内容描述: str
    状态: str = "pending"
    风险级别: str = "低"
    请求者: str = "system"
    创建时间: str = ""

class 内存存储:
    def __init__(self):
        self.流水线列表: dict[str, 流水线记录] = {}
        self.智能体列表: dict[str, 智能体记录] = {}
        self.审批列表: dict[str, 审批记录] = {}

    def 创建流水线(self, 名称: str, 描述: str) -> 流水线记录:
        r = 流水线记录(ID=f"pl-{uuid4()}", 名称=名称, 描述=描述, 创建时间=datetime.now().isoformat())
        self.流水线列表[r.ID] = r
        return r

    def 获取流水线(self, ID: str) -> 流水线记录 | None:
        return self.流水线列表.get(ID)

    def 获取所有流水线(self) -> list[流水线记录]:
        return list(self.流水线列表.values())

    def 查找智能体(self, ID: str) -> 智能体记录 | None:
        return self.智能体列表.get(ID)

    def 获取所有智能体(self) -> list[智能体记录]:
        return list(self.智能体列表.values())

    def 获取待审批(self) -> list[审批记录]:
        return [a for a in self.审批列表.values() if a.状态 == "pending"]

    def 获取所有审批(self) -> list[审批记录]:
        return list(self.审批列表.values())
```

- [ ] 创建 `内存存储` 类
- [ ] 实例化全局单例
- [ ] 预填充 3 个智能体记录（Claude Code / OpenCode / Codex）
- [ ] 验证 API 测试通过

#### Task 1.2: 接入流水线路由

**File:**
- Modify: `src/hermes/接口/路由/流水线路由.py`

```python
from ..存储 import 存储实例

@router.get("/", response_model=流水线列表响应)
async def 获取流水线列表(当前用户 = Depends(...)):
    列表 = 存储实例.获取所有流水线()
    return 流水线列表响应(
        流水线列表=[流水线响应(ID=p.ID, 名称=p.名称, 状态=p.状态, 阶段数=p.阶段数, 完成阶段数=p.完成阶段数) for p in 列表],
        总数=len(列表)
    )

@router.post("/", response_model=流水线响应, status_code=201)
async def 创建流水线(请求: 流水线创建请求, 当前用户 = Depends(...)):
    p = 存储实例.创建流水线(请求.名称, 请求.描述)
    return 流水线响应(ID=p.ID, 名称=p.名称, 状态=p.状态)

@router.get("/{pipeline_id}", response_model=流水线响应)
async def 获取流水线(pipeline_id: str, 当前用户 = Depends(...)):
    p = 存储实例.获取流水线(pipeline_id)
    if not p:
        raise HTTPException(status_code=404, detail="流水线不存在")
    return 流水线响应(ID=p.ID, 名称=p.名称, 状态=p.状态)
```

- [ ] 将所有 stub 返回值替换为 `存储实例` 调用
- [ ] 缺少记录时返回 404
- [ ] 运行 API 测试验证

#### Task 1.3: 接入智能体路由

**File:**
- Modify: `src/hermes/接口/路由/智能体路由.py`

接入 `存储实例`，预填充 3 个智能体。智能体健康检查返回真实状态。

#### Task 1.4: 接入审批路由 + Hermes 对话增强

**Files:**
- Modify: `src/hermes/接口/路由/审批路由.py`
- Modify: `src/hermes/接口/路由/hermes路由.py`

审批路由接入存储。Hermes 对话构建真实上下文（流水线统计 + 智能体状态 + 待审批数），调用 Claude Code 或返回有意义的回复。

---

### Phase 2: 前端功能性优化

#### Task 2.1: 新建流水线对话框

**File:**
- Modify: `web/src/pages/Pipelines.tsx`

添加"新建流水线"按钮 → 弹出对话框（名称、描述、模板选择）→ 调用 `api.pipeline.create()` → 刷新列表。

```tsx
import { useState } from 'react'
import { Dialog } from '@headlessui/react'

function CreatePipelineDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [loading, setLoading] = useState(false)

  const handleCreate = async () => {
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.pipeline.create({ 名称: name, 描述: desc, 流水线定义: {} })
      onClose()
      setName('')
      setDesc('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/60" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-[#1a1a2e] border border-white/10 rounded-xl p-6 w-full max-w-md">
          <Dialog.Title className="text-white/80 font-semibold mb-4">新建流水线</Dialog.Title>
          <input className="w-full mb-3 px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-sm text-white/60" placeholder="流水线名称" value={name} onChange={e => setName(e.target.value)} />
          <input className="w-full mb-4 px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-sm text-white/60" placeholder="描述（可选）" value={desc} onChange={e => setDesc(e.target.value)} />
          <div className="flex justify-end gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm text-white/40 hover:text-white/60">取消</button>
            <button onClick={handleCreate} disabled={loading || !name.trim()} className="px-4 py-2 text-sm bg-gradient-to-r from-[#6c5ce7] to-[#a29bfe] text-white rounded-lg disabled:opacity-50">创建</button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
```

#### Task 2.2: 流水线运行/取消操作

**File:**
- Modify: `web/src/pages/Pipelines.tsx`
- Modify: `web/src/pages/PipelineDetail.tsx`

给流水线卡片添加"运行"和"取消"按钮（现有 API 端点已就绪）。

#### Task 2.3: Dashboard 进度英雄区

**File:**
- Modify: `web/src/pages/Dashboard.tsx`

当前 Dashboard 是统计卡片列表。添加进度英雄区（类似原型 v2）显示活跃流水线的分步进度。

#### Task 2.4: HermesChat 真实对话

**File:**
- Modify: `web/src/components/layout/HermesChat.tsx`

当前 HermesChat 显示硬编码问候消息。改为从后端获取上下文初始化消息，输入框发送到 `api.hermes.chat()`。

---

### Phase 3: 质量加固

#### Task 3.1: 前端 Error Boundary

**File:**
- Create: `web/src/components/ErrorBoundary.tsx`

```tsx
import { Component, ReactNode } from 'react'

interface Props { children: ReactNode; fallback?: ReactNode }
interface State { hasError: boolean; error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }
  static getDerivedStateFromError(error: Error) { return { hasError: true, error } }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center h-full text-white/40 text-sm gap-3">
          <div>应用出现错误</div>
          <p className="text-xs text-white/20">{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })} className="px-3 py-1 bg-[#6c5ce7]/20 rounded text-xs text-[#a29bfe]">重试</button>
        </div>
      )
    }
    return this.props.children
  }
}
```

在 `Layout.tsx` 和各个页面中用 `<ErrorBoundary>` 包裹。

#### Task 3.2: 后端测试补充

**File:**
- Create: `tests/unit/test_接口_存储.py`
- Create: `tests/unit/test_接口_流水线.py`

```python
"""测试内存存储"""
from src.hermes.接口.存储 import 内存存储, 流水线记录

def test_创建和获取流水线():
    s = 内存存储()
    p = s.创建流水线("测试", "描述")
    assert p.ID is not None
    assert s.获取流水线(p.ID).名称 == "测试"
    assert s.获取流水线("不存在") is None
```

```python
"""测试流水线路由"""
from fastapi.testclient import TestClient
from src.hermes.接口.应用 import 应用

client = TestClient(应用)
headers = {"Authorization": "Bearer hermes-local-dev-key"}

def test_创建流水线_带认证():
    r = client.post("/流水线/", json={"名称": "t", "描述": "d", "流水线定义": {}}, headers=headers)
    assert r.status_code == 201
    assert r.json()["状态"] == "pending"

def test_创建流水线_无认证():
    r = client.post("/流水线/", json={"名称": "t", "描述": "d", "流水线定义": {}})
    assert r.status_code == 401
```

#### Task 3.3: 前端 TypeScript 严格模式

**File:**
- Modify: `web/tsconfig.app.json`

启用 `strict: true`，修复所有类型错误。所有 `as Record<string, unknown>` 断言替换为具体类型。

---

### Phase 4: 用户体验打磨

#### Task 4.1: 页面过渡动画

```tsx
// 在 Layout.tsx 中添加简单的 fade 过渡
<main className="flex-1 overflow-auto p-6 animate-fadeIn">
  <Outlet />
</main>
```

CSS:
```css
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.animate-fadeIn { animation: fadeIn 0.2s ease-out; }
```

#### Task 4.2: 智能体实时状态轮询

**Files:**
- Modify: `web/src/pages/Agents.tsx`

使用 `refetchInterval: 5000` 自动刷新智能体状态，在线/离线指示灯动画。

#### Task 4.3: 配置页面样式统一

当前 Config 页面使用旧版 `dark-*`/`accent-*` 颜色体系。统一为桌面应用的紫色主题。

---

### Phase 5: 部署与文档

#### Task 5.1: Electron 打包脚本

验证 `electron-builder` 配置，编写一键打包脚本：
```bash
cd web
npm run dist   # 构建 + 打包为安装包
```

#### Task 5.2: Python 后端启动脚本

创建 `scripts/start-backend.ps1`：
```powershell
$env:PYTHONPATH = "C:\Ai\起源信标\ResonanceBeacon\src"
python -m uvicorn hermes.接口.应用:应用 --host 127.0.0.1 --port 8765 --reload
```

#### Task 5.3: README 更新

更新 `web/README.md` 包含桌面应用启动说明、打包说明。
