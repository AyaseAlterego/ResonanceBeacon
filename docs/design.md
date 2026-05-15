# 起源信标 — 项目工作流设计文档

**日期**: 2026-05-12
**版本**: 2.0
**状态**: 设计中

---

## 1. 背景与问题

当前系统的"新建流水线"按钮点击后只是往内存里插入一条空记录，没有连接到编排器引擎，也没有和 Hermes 元智能体产生任何交互。整个系统缺少"项目"这一核心实体的完整生命周期。

用户期望的流程是：

**新建项目 → 和 Hermes 聊需求 → 输出设计文档/蓝图/原型 → 确认 → 调度 opencode 开发**

现状的关键问题：

| 问题 | 现状 | 期望 |
|------|------|------|
| 项目实体 | ORM 模型存在但未接线 | 项目作为一等公民，贯穿整个生命周期 |
| Hermes 聊天 | 无状态、纯信息问答、对话不持久化 | 有状态、可驱动阶段推进、对话持久化 |
| 阶段推进 | 无 | 需求→设计→确认→开发，有明确的阶段转换 |
| 制品产出 | 无 | 每个阶段产出制品并存储 |
| 开发调度 | 无 | 确认后自动生成流水线定义并调度 opencode |
| 方法论 | 无 | 融入 Superpowers 的技能驱动开发方法论 |

---

## 2. Superpowers 融合设计

### 2.1 Superpowers 是什么

[Superpowers](https://github.com/obra/superpowers) 是一个 AI 编码智能体的技能框架和软件开发方法论。它的核心工作流是：

```
brainstorming → writing-plans → subagent-driven-development → finishing-a-development-branch
```

每个技能都是**强制的**，不是建议。智能体在执行任何任务前必须检查是否有相关技能适用。

### 2.2 融合策略：Hermes = Superpowers 的编排者

核心思路：**Hermes 不是在对话中模拟开发流程，而是真正驱动 Superpowers 的技能链**。

在 Superpowers 原生工作流中，这些技能运行在编码智能体（Claude Code / OpenCode）内部。融合后：

| Superpowers 技能 | 在起源信标中的角色 | 执行者 |
|---|---|---|
| **brainstorming** | 对应项目的「需求分析」阶段 | Hermes 在对话中执行 |
| **writing-plans** | 对应项目的「架构设计」阶段 | Hermes 产出设计文档 + 实施计划 |
| **using-git-worktrees** | 开发执行的前置步骤 | OpenCode 智能体执行 |
| **subagent-driven-development** | 对应项目的「开发执行」阶段 | OpenCode 智能体执行 |
| **test-driven-development** | 开发执行中的质量守卫 | OpenCode 子智能体执行 |
| **systematic-debugging** | 开发过程中的调试 | OpenCode 子智能体执行 |
| **requesting-code-review** | 开发完成后的审查 | OpenCode 子智能体执行 |
| **finishing-a-development-branch** | 开发收尾 | OpenCode 智能体执行 |
| **verification-before-completion** | 完成验证 | OpenCode 子智能体执行 |

### 2.3 技能作为项目阶段的驱动核心

项目的阶段不再是抽象的状态标签，而是 **Superpowers 技能的具体执行**：

```
项目阶段             对应技能                    执行方式
────────────────────────────────────────────────────────────
需求分析        ←→  brainstorming          →  Hermes 对话驱动
架构设计        ←→  writing-plans          →  Hermes 产出 spec + plan
方案确认        ←→  用户审批 gate          →  人类确认 spec 和 plan
开发执行        ←→  subagent-driven-dev    →  OpenCode 智能体执行 plan
代码审查        ←→  requesting-code-review →  OpenCode 子智能体审查
完成            ←→  finishing-a-branch     →  OpenCode 智能体收尾
```

### 2.4 技能注入机制

Hermes 在调度智能体执行任务时，将 Superpowers 技能作为 **任务上下文的一部分注入**：

```python
def 构建任务上下文(项目: 项目记录, 任务: 任务记录, 制品列表: list[制品记录]) -> str:
    上下文 = f"项目: {项目.名称}\n"

    for 制品 in 制品列表:
        上下文 += f"\n--- {制品.名称} ---\n{制品.内容}\n"

    # 注入 Superpowers 技能指令
    if 任务.类别 == "code_generation":
        上下文 += "\n--- 必须遵循的方法论 ---\n"
        上下文 += "你必须使用 test-driven-development 技能：先写失败测试，再写最小实现代码。\n"
        上下文 += "不要跳过 RED 阶段。如果没有看到测试失败，你不知道测试的是否正确。\n"

    return 上下文
```

### 2.5 技能文件部署

Superpowers 的技能定义文件（SKILL.md）需要被部署到 OpenCode 的工作目录中，使其能自动发现和加载：

```
项目工作目录/
├── .opencode/
│   └── INSTALL.md           # OpenCode 的 Superpowers 安装指引
├── CLAUDE.md                 # Claude Code 的项目级指令
├── AGENTS.md                 # 智能体行为约定
├── docs/
│   ├── specs/                # 设计文档（brainstorming 产出）
│   └── plans/                # 实施计划（writing-plans 产出）
└── src/                      # 代码（开发执行产出）
```

Hermes 在创建项目工作目录时，自动部署 Superpowers 配置文件。这样当 OpenCode 智能体被调度到该项目工作时，它会自动加载并遵循 Superpowers 的技能链。

---

## 3. 设计概览

### 3.1 核心概念

```
项目 (Project)
 ├── 阶段状态: 需求分析 → 架构设计 → 方案确认 → 开发执行 → 代码审查 → 完成
 ├── 阶段 = Superpowers 技能的具体执行
 ├── 对话 (Conversation)
 │    └── 消息列表 (Messages) — 持久化，Hermes 可读完整上下文
 ├── 制品 (Artifacts) — 对应 Superpowers 的产出物
 │    ├── spec（需求文档）   ← brainstorming 产出
 │    ├── plan（实施计划）   ← writing-plans 产出
 │    ├── code（代码）       ← subagent-driven-development 产出
 │    └── review（审查报告） ← requesting-code-review 产出
 ├── 工作目录 (Workspace) — 项目对应的文件系统目录
 │    ├── .opencode/         # Superpowers 技能配置
 │    ├── CLAUDE.md          # 项目级智能体指令
 │    ├── docs/specs/        # spec 制品落地
 │    └── docs/plans/        # plan 制品落地
 └── 流水线 (Pipeline) — 确认后由 Hermes 自动创建并调度
```

### 3.2 项目阶段状态机（Superpowers 映射）

```
需求分析           架构设计           方案确认           开发执行           代码审查           完成
(brainstorming)    (writing-plans)   (human gate)       (subagent-dev)     (code-review)      (finishing)
     │                  │                  │                  │                  │               │
     │ Hermes 引导      │ Hermes 产出      │ 用户审批          │ OpenCode 执行     │ 子智能体审查    │
     │ 需求讨论         │ spec + plan      │ spec + plan      │ plan 中的任务     │ spec合规+质量   │
     │                  │                  │                  │ TDD 强制          │                  │
     ▼                  ▼                  ▼                  ▼                  ▼               ▼
 [SUBMIT_SPEC]    [SUBMIT_PLAN]      [APPROVE/REJECT]   [TASK_DISPATCH]   [REVIEW_RESULT]  [DONE]
```

每个阶段转换时：
- Hermes/智能体根据技能规范产出制品
- 前端弹出确认面板，展示制品内容
- 用户确认 → 进入下一阶段；用户修改 → 回到对话继续讨论
- 制品同时落地到项目工作目录的对应位置

---

## 4. 数据模型

### 4.1 后端存储层改造

#### 项目记录

```python
@dataclass
class 项目记录:
    ID: str                          # "proj-{uuid4}"
    名称: str
    描述: str = ""
    阶段: str = "需求分析"            # 需求分析|架构设计|方案确认|开发执行|代码审查|完成|已取消|失败
    仓库URL: str = ""
    工作目录: str = ""                # 项目对应的文件系统路径
    配置: dict = field(default_factory=dict)
    创建时间: str = ""
    更新时间: str = ""
```

#### 对话记录

```python
@dataclass
class 对话记录:
    ID: str                          # "conv-{uuid4}"
    项目ID: str                      # FK → 项目记录.ID
    创建时间: str = ""
```

#### 消息记录

```python
@dataclass
class 消息记录:
    ID: str                          # "msg-{uuid4}"
    对话ID: str                      # FK → 对话记录.ID
    角色: str                        # "user" | "hermes" | "system"
    内容: str
    元数据: dict = field(default_factory=dict)  # 阶段、制品引用、技能名称等
    创建时间: str = ""
```

#### 制品记录

```python
@dataclass
class 制品记录:
    ID: str                          # "art-{uuid4}"
    项目ID: str                      # FK → 项目记录.ID
    制品类型: str                    # spec|plan|code|review
    名称: str
    内容: str                        # Markdown 格式
    阶段: str                        # 产出该制品的项目阶段
    技能: str                        # 产出该制品的 Superpowers 技能名
    文件路径: str = ""               # 落地到工作目录的路径
    创建时间: str = ""
```

### 4.2 内存存储扩展

```python
class 内存存储:
    def __init__(self):
        # 现有
        self.流水线列表: dict[str, 流水线记录] = {}
        self.智能体列表: dict[str, 智能体记录] = {}
        self.审批列表: dict[str, 审批记录] = {}
        # 新增
        self.项目列表: dict[str, 项目记录] = {}
        self.对话列表: dict[str, 对话记录] = {}
        self.消息列表: dict[str, list[消息记录]] = {}
        self.制品列表: dict[str, 制品记录] = {}

    # 项目 CRUD
    def 创建项目(self, 名称: str, 描述: str = "") -> 项目记录
    def 获取项目(self, ID: str) -> 项目记录 | None
    def 获取所有项目(self) -> list[项目记录]
    def 更新项目阶段(self, ID: str, 阶段: str) -> 项目记录 | None

    # 对话
    def 创建对话(self, 项目ID: str) -> 对话记录
    def 获取项目对话(self, 项目ID: str) -> 对话记录 | None

    # 消息
    def 添加消息(self, 对话ID: str, 角色: str, 内容: str, 元数据: dict = None) -> 消息记录
    def 获取对话消息(self, 对话ID: str) -> list[消息记录]

    # 制品
    def 创建制品(self, 项目ID: str, 制品类型: str, 名称: str, 内容: str, 阶段: str, 技能: str) -> 制品记录
    def 获取项目制品(self, 项目ID: str) -> list[制品记录]
```

---

## 5. API 设计

### 5.1 项目路由 — `/项目/`

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/项目/` | 列出所有项目 |
| POST | `/项目/` | 创建项目 |
| GET | `/项目/{id}` | 获取项目详情 |
| PUT | `/项目/{id}/阶段` | 更新项目阶段 |

创建项目时自动创建对话记录和工作目录（含 Superpowers 配置文件部署）。

### 5.2 对话路由 — `/项目/{项目ID}/对话/`

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/项目/{项目ID}/对话/` | 获取项目对话（含消息历史） |
| POST | `/项目/{项目ID}/对话/消息` | 发送消息给 Hermes |

发送消息的响应：

```json
{
  "用户消息": { "ID": "msg-xxx", "角色": "user", "内容": "...", "创建时间": "..." },
  "Hermes回复": { "ID": "msg-yyy", "角色": "hermes", "内容": "...", "创建时间": "..." },
  "项目阶段": "需求分析",
  "阶段产出": null,
  "技能状态": {
    "当前技能": "brainstorming",
    "技能阶段": "clarifying_questions",
    "可推进": false
  }
}
```

当 Hermes 判断阶段可以推进时，响应包含 `阶段产出`：

```json
{
  "用户消息": { ... },
  "Hermes回复": { "ID": "msg-yyy", "角色": "hermes", "内容": "需求分析完成，请查看设计文档", "创建时间": "..." },
  "项目阶段": "需求分析",
  "阶段产出": {
    "制品ID": "art-xxx",
    "制品类型": "spec",
    "名称": "项目设计文档",
    "内容": "# 设计文档\n\n## 1. 项目概述\n...",
    "技能": "brainstorming"
  },
  "技能状态": {
    "当前技能": "brainstorming",
    "技能阶段": "design_approved",
    "可推进": true
  }
}
```

### 5.3 制品路由 — `/项目/{项目ID}/制品/`

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/项目/{项目ID}/制品/` | 列出项目所有制品 |
| GET | `/项目/{项目ID}/制品/{制品ID}` | 获取制品详情 |

### 5.4 阶段确认路由 — `/项目/{项目ID}/确认`

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/项目/{项目ID}/确认` | 确认当前阶段，推进到下一阶段 |
| POST | `/项目/{项目ID}/拒绝` | 拒绝当前阶段产出，回到对话 |

确认阶段时：
- 制品落地到项目工作目录（spec → `docs/specs/`，plan → `docs/plans/`）
- 从"方案确认"推进到"开发执行"时，自动创建流水线并触发执行

---

## 6. Hermes 行为设计（Superpowers 技能驱动）

### 6.1 阶段 = 技能执行

Hermes 的 system prompt 不再是简单的阶段描述，而是**嵌入完整的 Superpowers 技能定义**：

**需求分析阶段（brainstorming 技能）**：
```
你是 Hermes，起源信标系统的元智能体。当前项目处于「需求分析」阶段。

你必须遵循 brainstorming 技能：

## 流程
1. 探索项目上下文 — 了解现有代码、文档、最近提交
2. 一次问一个澄清问题 — 理解目的、约束、成功标准
3. 提出2-3种方案 — 附带权衡和你的推荐
4. 分段呈现设计 — 每段确认后再继续
5. 输出设计文档 — 用 [SUBMIT_SPEC]...[/SUBMIT_SPEC] 包裹

## 硬约束
- 在呈现设计并获得用户批准之前，不进入任何实现
- 每个项目都走这个流程，不论看起来多简单
- YAGNI：从所有设计中移除不必要的功能

项目信息：{项目名称} - {项目描述}
对话历史：{历史消息}
```

**架构设计阶段（writing-plans 技能）**：
```
你是 Hermes，起源信标系统的元智能体。当前项目处于「架构设计」阶段。

设计文档已经确认：{spec内容}

你必须遵循 writing-plans 技能：

## 流程
1. 映射文件结构 — 哪些文件需要创建或修改
2. 分解为2-5分钟的 bite-sized 任务
3. 每个任务包含：精确文件路径、完整代码、验证步骤
4. 强制 TDD：先写失败测试 → 验证失败 → 写最小实现 → 验证通过 → 提交
5. 输出实施计划 — 用 [SUBMIT_PLAN]...[/SUBMIT_PLAN] 包裹

## 硬约束
- 不允许占位符：每个步骤必须包含实际内容
- DRY, YAGNI, TDD, 频繁提交
- 精确文件路径，完整代码，精确命令

已有设计文档：{spec内容}
```

**方案确认阶段（human gate）**：
```
你是 Hermes，起源信标系统的元智能体。当前项目处于「方案确认」阶段。

你需要汇总所有制品，向用户展示完整方案：

## 展示内容
1. 设计文档（spec）— brainstorming 产出
2. 实施计划（plan）— writing-plans 产出
3. 文件结构映射
4. 预估任务数和时间

## 关键问题
- 需求是否完整覆盖？
- 技术选型是否合理？
- 实施计划是否可执行？
- 是否需要分解为子项目？

确认后将自动进入开发阶段，OpenCode 智能体将按计划执行。
```

**开发执行阶段（subagent-driven-development 技能）**：
```
你是 Hermes，起源信标系统的元智能体。当前项目处于「开发执行」阶段。

OpenCode 智能体正在按照实施计划执行开发。你不需要编写代码。

你的任务是监控和协调：
1. 汇报开发进度（当前执行到哪个任务）
2. 转达智能体遇到的问题给用户决策
3. 开发完成后通知用户进入代码审查阶段

## 智能体执行规则
- 每个任务由独立子智能体执行（fresh context）
- 强制 TDD：RED → GREEN → REFACTOR
- 每个任务完成后两阶段审查：spec合规 + 代码质量
- 审查发现问题 → 修复 → 重新审查
```

### 6.2 制品提取逻辑

```python
import re

制品标记模式 = {
    "需求分析": (r"\[SUBMIT_SPEC\](.*?)\[/SUBMIT_SPEC\]", "spec", "设计文档", "brainstorming"),
    "架构设计": (r"\[SUBMIT_PLAN\](.*?)\[/SUBMIT_PLAN\]", "plan", "实施计划", "writing-plans"),
}
```

后端解析 Hermes 回复时：
1. 检测是否包含制品标记
2. 提取制品内容，存入制品表
3. 同时将制品落地到项目工作目录（spec → `docs/specs/`，plan → `docs/plans/`）
4. 在响应中返回 `阶段产出` 字段
5. 前端弹出确认面板

### 6.3 Superpowers 配置自动部署

创建项目时，自动在工作目录中部署 Superpowers 配置：

```python
def 部署Superpowers配置(工作目录: str):
    os.makedirs(os.path.join(工作目录, ".opencode"), exist_ok=True)
    os.makedirs(os.path.join(工作目录, "docs", "specs"), exist_ok=True)
    os.makedirs(os.path.join(工作目录, "docs", "plans"), exist_ok=True)

    # 写入 AGENTS.md — 项目级智能体指令
    with open(os.path.join(工作目录, "AGENTS.md"), "w", encoding="utf-8") as f:
        f.write("""# 项目智能体指令

## 必须遵循的技能
- brainstorming: 在任何创意工作之前使用
- test-driven-development: 实现任何功能时使用
- systematic-debugging: 遇到 bug 时使用
- verification-before-completion: 声称完成之前验证

## 方法论
- TDD: 先写测试，看它失败，再写实现
- YAGNI: 不需要的不要加
- DRY: 不要重复自己
- 频繁提交
""")
```

### 6.4 流水线自动生成（Superpowers 技能链）

当项目从"方案确认"推进到"开发执行"时，生成的流水线定义直接映射 Superpowers 技能链：

```python
def 生成开发流水线(项目: 项目记录, 制品列表: list[制品记录]) -> dict:
    spec = next((a for a in 制品列表 if a.制品类型 == "spec"), None)
    plan = next((a for a in 制品列表 if a.制品类型 == "plan"), None)

    return {
        "名称": f"{项目.名称} - 开发",
        "描述": "基于设计文档和实施计划的 Superpowers 技能驱动开发",
        "流水线定义": {
            "stages": [
                {
                    "id": "setup",
                    "name": "工作区准备",
                    "type": "sequential",
                    "技能": "using-git-worktrees",
                    "tasks": [
                        {
                            "id": "worktree",
                            "name": "创建隔离工作区",
                            "type": "workspace_setup",
                            "category": "utility",
                            "context": {"spec": spec.内容, "plan": plan.内容}
                        }
                    ]
                },
                {
                    "id": "development",
                    "name": "开发实现",
                    "type": "sequential",
                    "技能": "subagent-driven-development",
                    "tasks": _从计划提取任务(plan)
                },
                {
                    "id": "review",
                    "name": "代码审查",
                    "type": "sequential",
                    "技能": "requesting-code-review",
                    "tasks": [
                        {
                            "id": "spec_review",
                            "name": "Spec 合规审查",
                            "type": "code_review",
                            "category": "advisor",
                            "context": {"spec": spec.内容}
                        },
                        {
                            "id": "quality_review",
                            "name": "代码质量审查",
                            "type": "code_review",
                            "category": "advisor"
                        }
                    ]
                },
                {
                    "id": "finishing",
                    "name": "开发收尾",
                    "type": "sequential",
                    "技能": "finishing-a-development-branch",
                    "tasks": [
                        {
                            "id": "verify",
                            "name": "完成验证",
                            "type": "verification",
                            "category": "utility",
                            "技能": "verification-before-completion"
                        }
                    ]
                }
            ]
        }
    }
```

### 6.5 任务执行时的技能注入

当编排器引擎调度 OpenCode 智能体执行开发任务时，注入 Superpowers 技能指令：

```python
def 构建任务提示(任务: 任务记录, 项目: 项目记录, 制品列表: list[制品记录]) -> str:
    提示 = f"项目: {项目.名称}\n\n"

    for 制品 in 制品列表:
        提示 += f"--- {制品.名称} ---\n{制品.内容}\n\n"

    提示 += f"--- 当前任务 ---\n{任务.名称}\n{任务.输入数据}\n\n"

    # 根据任务类型注入 Superpowers 技能
    技能注入 = {
        "code_generation": """
你必须遵循 test-driven-development 技能：
1. RED: 先写一个失败测试
2. 验证测试失败（MANDATORY，不可跳过）
3. GREEN: 写最小代码使测试通过
4. 验证测试通过
5. REFACTOR: 清理代码
6. 所有测试仍然通过

如果你在写测试之前写了实现代码，删除它，从头开始。
""",
        "bug_fix": """
你必须遵循 systematic-debugging 技能：
Phase 1: 根因调查 — 仔细阅读错误信息，稳定复现，检查最近变更
Phase 2: 模式分析 — 找到正常工作的类似代码，对比差异
Phase 3: 假设与测试 — 提出单一假设，最小化测试
Phase 4: 实施 — 先写失败测试，再修复根因

不要在完成 Phase 1 之前提出任何修复。
""",
    }

    提示 += 技能注入.get(任务.类别, "")
    return 提示
```

---

## 7. 前端设计

### 7.1 路由变更

```
/                        → Dashboard（项目概览 + 新建项目入口）
/projects                → Projects（项目列表页）
/projects/:id            → ProjectDetail（项目详情页 — 核心页面）
/pipelines               → Pipelines（保留，流水线列表）
/pipelines/:id           → PipelineDetail（保留，流水线详情）
/agents                  → Agents（保留）
/approvals               → Approvals（保留）
/config                  → Config（保留）
```

### 7.2 项目详情页 — 核心页面

```
┌──────────────────────────────────────────────────────────────────────┐
│ 项目名称                            阶段: 需求分析 ▶ 架构设计         │
│ 技能: brainstorming                                                  │
├──────────────────────────────────────┬───────────────────────────────┤
│                                      │                               │
│  对话面板 (70%)                       │  制品 + 技能面板 (30%)          │
│                                      │                               │
│  ┌──────────────────────────────┐   │  📋 技能进度                    │
│  │ Hermes: 你好！告诉我你想做    │   │  ● brainstorming ✓             │
│  │ 什么项目？                    │   │  ○ writing-plans               │
│  └──────────────────────────────┘   │  ○ human-gate                  │
│  ┌──────────────────────────────┐   │  ○ subagent-driven-dev         │
│  │ 你: 我想做一个博客系统       │   │  ○ code-review                 │
│  └──────────────────────────────┘   │  ○ finishing                   │
│  ┌──────────────────────────────┐   │                               │
│  │ Hermes: 好的，让我了解更多... │   │  ──────────────                │
│  └──────────────────────────────┘   │  📄 制品                       │
│                                      │  ✦ 设计文档 (spec)             │
│  ┌──────────────────────────────┐   │  ✦ 实施计划 (plan)             │
│  │ [输入消息...]          [发送] │   │  ✦ 代码 (code)                │
│  └──────────────────────────────┘   │  ✦ 审查报告 (review)           │
│                                      │                               │
├──────────────────────────────────────┴───────────────────────────────┤
│                                                                      │
│  阶段确认面板 (弹出，当技能产出制品时)                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 📋 brainstorming 技能产出：设计文档                            │   │
│  │ ┌──────────────────────────────────────────────────────────┐ │   │
│  │ │ # 设计文档                                               │ │   │
│  │ │ ## 1. 项目概述                                           │ │   │
│  │ │ 博客系统，支持文章发布、评论、标签...                     │ │   │
│  │ └──────────────────────────────────────────────────────────┘ │   │
│  │                              [继续修改]  [确认并进入下一阶段]    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.3 组件结构

```
pages/
  Projects.tsx              项目列表页
  ProjectDetail.tsx         项目详情页（核心）
  ProjectConversation.tsx   对话面板组件
  ProjectArtifacts.tsx      制品面板组件
  StageConfirmPanel.tsx     阶段确认弹出面板
  SkillProgress.tsx         Superpowers 技能进度条（替代简单的阶段进度）

components/
  ArtifactCard.tsx          制品卡片
  SkillBadge.tsx            技能状态徽章（显示当前技能名+阶段）
  SkillTimeline.tsx         技能执行时间线
```

### 7.4 TypeScript 类型扩展

```typescript
export type ProjectStage =
  | '需求分析'
  | '架构设计'
  | '方案确认'
  | '开发执行'
  | '代码审查'
  | '完成'
  | '已取消'
  | '失败';

export type ArtifactType = 'spec' | 'plan' | 'code' | 'review';

export type SuperpowersSkill =
  | 'brainstorming'
  | 'writing-plans'
  | 'using-git-worktrees'
  | 'subagent-driven-development'
  | 'test-driven-development'
  | 'requesting-code-review'
  | 'finishing-a-development-branch'
  | 'systematic-debugging'
  | 'verification-before-completion';

export interface SkillStatus {
  当前技能: SuperpowersSkill;
  技能阶段: string;
  可推进: boolean;
}

export interface Project {
  ID: string;
  名称: string;
  描述: string;
  阶段: ProjectStage;
  工作目录: string;
  创建时间: string;
  更新时间: string;
}

export interface Artifact {
  ID: string;
  项目ID: string;
  制品类型: ArtifactType;
  名称: string;
  内容: string;
  阶段: ProjectStage;
  技能: SuperpowersSkill;
  文件路径: string;
  创建时间: string;
}

export interface ChatResponse {
  用户消息: ConversationMessage;
  Hermes回复: ConversationMessage;
  项目阶段: ProjectStage;
  阶段产出: Artifact | null;
  技能状态: SkillStatus;
}
```

---

## 8. 实施步骤

### Phase 1: 后端基础（项目 + 对话 + 制品存储）

1. 扩展 `接口/存储.py`：添加项目、对话、消息、制品的数据类和 CRUD 方法
2. 新增 `接口/路由/项目路由.py`：项目 CRUD + 阶段更新
3. 新增 `接口/路由/对话路由.py`：对话消息 + Hermes 回复（含技能状态）
4. 新增 `接口/路由/制品路由.py`：制品查询
5. 在 `接口/应用.py` 中注册新路由
6. 改造 `hermes路由.py`：多轮对话上下文 + 阶段感知 prompt（嵌入 Superpowers 技能定义）+ 制品标记解析
7. 实现项目创建时的 Superpowers 配置自动部署

### Phase 2: 前端核心（项目详情页 + 对话）

1. 新增 TypeScript 类型定义（含 SkillStatus 等）
2. 扩展 API Client
3. 新增 `Projects.tsx` 项目列表页
4. 新增 `ProjectDetail.tsx` 项目详情页
5. 新增 `ProjectConversation.tsx` 对话面板
6. 新增 `ProjectArtifacts.tsx` 制品面板
7. 新增 `StageConfirmPanel.tsx` 阶段确认面板
8. 新增 `SkillProgress.tsx` 技能进度条
9. 更新路由配置
10. 改造 Dashboard 为项目概览

### Phase 3: Superpowers 技能集成

1. 实现完整的 Superpowers 技能 prompt 模板系统
2. 实现制品标记解析、存储和文件落地
3. 实现确认/拒绝的阶段转换逻辑
4. 实现"方案确认→开发执行"时的流水线自动生成（技能链映射）
5. 实现任务执行时的技能注入
6. 连接编排器引擎执行开发流水线

### Phase 4: 全局面板整合

1. 改造 Layout.tsx：项目详情页时隐藏全局 HermesChat
2. 改造全局 HermesChat：支持项目快速跳转
3. 改造 NavRail：新增项目入口图标
4. 改造 Sidebar：展示活跃项目列表

---

## 9. 与现有代码的兼容性

- 现有流水线（`/流水线/`）相关 API 和页面**保留不变**
- 项目创建的流水线复用现有的 `流水线记录` 和流水线 API
- 现有审批系统在方案确认阶段自然接入
- 全局 HermesChat 在非项目页面保持原有行为
- 智能体系统（注册表、适配器、类别路由）在开发执行阶段被编排器引擎调用
- Superpowers 技能以 prompt 注入方式集成，不需要修改 OpenCode/Claude Code 的代码

---

## 10. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| Hermes AI 回复格式不稳定，制品标记可能解析失败 | 多层回退：精确匹配 → 宽松匹配 → 整段内容作为制品 |
| 内存存储不持久化，重启丢失 | Phase 1 先用内存存储快速验证，后续接入 SQLite/PostgreSQL |
| 对话历史过长导致 token 超限 | 滑动窗口：最近 N 条消息完整 + 更早消息摘要 |
| 开发执行阶段 opencode 调度失败 | 熔断器 + 重试 + 通知用户手动干预 |
| Superpowers 技能 prompt 过长消耗 token | 技能定义按需注入，只注入当前阶段对应的技能 |
| OpenCode 未安装 Superpowers 插件 | 项目创建时检测并提示安装；技能通过 prompt 注入兜底 |
