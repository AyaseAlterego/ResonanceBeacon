# 智能体接入指南

起源信标 (ResonanceBeacon) 智能体系统接入与开发完整指南。

---

## 目录

- [1. 系统架构概述](#1-系统架构概述)
- [2. 核心数据结构](#2-核心数据结构)
- [3. 智能体适配器接口](#3-智能体适配器接口)
- [4. 类别路由系统](#4-类别路由系统)
- [5. 注册表与健康检查机制](#5-注册表与健康检查机制)
- [6. 现有适配器接口说明](#6-现有适配器接口说明)
- [7. 新适配器接入完整示例](#7-新适配器接入完整示例)

---

## 1. 系统架构概述

起源信标的智能体层采用**基于类别的智能体路由**模式。Hermes Agent 作为元智能体，不直接指定使用哪个智能体，而是通过**类别**来描述任务需求，由类别路由器自动选择最佳智能体。

### 架构分层

```
                    ┌─────────────┐
                    │  流水线引擎   │  提交任务 + 类别
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  类别路由器   │  根据 类别+任务需求 选择智能体
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  智能体注册表  │  管理所有智能体实例和工厂
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │Claude Code  │ │  OpenCode   │ │   Codex     │  ...可扩展
    │   适配器     │ │   适配器     │ │   适配器     │
    └─────────────┘ └─────────────┘ └─────────────┘
```

### 核心设计原则

1. **类别驱动路由**：调用方只声明"我需要什么类别的智能体"，无需关心具体实现
2. **工厂 + 依赖注入**：智能体通过工厂创建，支持配置注入和测试替换
3. **安全创建模式**：`安全创建适配器()` 捕获所有异常，单个智能体失败不影响系统
4. **评分选择**：路由器对候选智能体多维评分，返回最佳匹配

### 源码结构

```
src/hermes/智能体/
├── __init__.py          # 模块导出
├── 基础.py              # 抽象基类、枚举、数据结构
├── 注册表.py             # 智能体注册表
├── 类别.py               # 类别路由器
├── 健康检查.py            # 健康检查器与负载统计
├── 上下文管理器.py         # 令牌预算与上下文管理
├── 提示词模板.py           # 提示词模板管理器
└── 适配器/
    ├── __init__.py       # 适配器导出
    ├── claude_code.py    # Claude Code 适配器
    ├── opencode.py       # OpenCode 适配器
    └── codex.py          # Codex 适配器
```

---

## 2. 核心数据结构

所有数据结构定义在 `src/hermes/智能体/基础.py` 中。

### 2.1 枚举类型

#### 智能体类别（`智能体类别`）

8 个类别，用于路由选择：

| 类别 | 枚举值 | 用途 |
|------|--------|------|
| 超级大脑 | `ultrabrain` | 架构级、高难度逻辑推理 |
| 深度 | `deep` | 深度代码生成、复杂实现 |
| 快速 | `quick` | 快速响应、简单任务 |
| 视觉工程 | `visual-engineering` | 前端、UI、视觉相关开发 |
| 专家 | `specialist` | 特定领域专长任务 |
| 探索 | `exploration` | 代码探索、需求分析 |
| 顾问 | `advisor` | 咨询、审查、评估 |
| 工具 | `utility` | 通用工具类任务 |

#### 智能体成本（`智能体成本`）

| 层级 | 枚举值 | 含义 |
|------|--------|------|
| 免费 | `FREE` | 无 API 成本 |
| 便宜 | `CHEAP` | 低成本 |
| 昂贵 | `EXPENSIVE` | 高成本 |

#### 智能体健康状态（`智能体健康状态`）

| 状态 | 枚举值 | 含义 |
|------|--------|------|
| 健康 | `healthy` | 正常运行 |
| 降级 | `degraded` | 部分功能受限 |
| 不健康 | `unhealthy` | 不可用 |

### 2.2 数据类

#### `智能体能力`

描述智能体的一项能力：

```python
@dataclass
class 智能体能力:
    名称: str                                    # 能力名称，如 "code_generation"
    语言列表: list[str] = field(default_factory=list)  # 支持的编程语言
    上下文窗口: int = 200000                      # 上下文窗口大小（令牌数）
    每千令牌成本: float = 0.0                     # 每千令牌成本
    最大并发任务数: int = 5                        # 最大并发任务数
```

#### `任务结果`

任务执行完成后的返回值：

```python
@dataclass
class 任务结果:
    任务ID: str                                  # 任务唯一标识
    状态: str                                    # "completed" | "failed" | "cancelled"
    输出数据: dict[str, Any] = field(default_factory=dict)  # 输出数据
    制品列表: list[dict[str, Any]] = field(default_factory=list)  # 产出制品
    使用的令牌数: int = 0                          # 令牌消耗
    成本: float = 0.0                             # 成本
    耗时毫秒: int = 0                             # 执行耗时
    错误: Optional[str] = None                    # 错误信息
```

#### `任务需求`

用于智能体选择的需求描述：

```python
@dataclass
class 任务需求:
    能力列表: list[str] = field(default_factory=list)  # 所需能力名称列表
    预估令牌数: int = 0                              # 预估令牌消耗
    所需语言: Optional[str] = None                    # 所需编程语言
    优先级: int = 0                                  # 0-10，10最高
```

#### `上下文包`

传递给智能体的执行上下文：

```python
@dataclass
class 上下文包:
    流水线ID: str = ""
    阶段ID: str = ""
    任务ID: str = ""
    输入数据: dict[str, Any] = field(default_factory=dict)
    之前的制品: list[dict[str, Any]] = field(default_factory=list)
    元数据: dict[str, Any] = field(default_factory=dict)
```

---

## 3. 智能体适配器接口

### 3.1 `智能体适配器` 抽象基类

所有智能体适配器**必须**继承 `智能体适配器` 并实现以下抽象成员：

```python
class 智能体适配器(ABC):

    # ── 属性（必须实现） ──

    @property
    @abstractmethod
    def 智能体ID(self) -> str:
        """智能体唯一标识，如 "claude_code"、"opencode"、"codex" """

    @property
    @abstractmethod
    def 能力列表(self) -> list[智能体能力]:
        """该智能体提供的能力列表"""

    @property
    @abstractmethod
    def 类别(self) -> 智能体类别:
        """智能体的主要类别"""

    @property
    @abstractmethod
    def 成本层级(self) -> 智能体成本:
        """成本层级：FREE / CHEAP / EXPENSIVE"""

    # ── 方法（必须实现） ──

    @abstractmethod
    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化智能体（如建立 API 连接、加载配置）"""

    @abstractmethod
    async def 健康检查(self) -> bool:
        """执行健康检查，返回智能体是否可用"""

    @abstractmethod
    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        """执行单个任务，返回任务结果"""

    @abstractmethod
    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行任务，逐步 yield 增量结果"""

    @abstractmethod
    async def 取消任务(self, 任务ID: str) -> bool:
        """取消正在执行的任务，返回是否成功"""
```

### 3.2 `智能体工厂` 抽象基类

工厂用于创建适配器实例，配合注册表使用：

```python
class 智能体工厂(ABC):

    @property
    @abstractmethod
    def 智能体ID(self) -> str:
        """工厂创建的智能体ID"""

    @abstractmethod
    def 创建(self, 模型: str, 配置: dict[str, Any]) -> 智能体适配器:
        """创建智能体适配器实例"""
```

### 3.3 `安全创建适配器` 函数

包装工厂创建的安全函数。创建失败时返回 `None` 而不是抛出异常，确保一个智能体失败不影响整个系统：

```python
def 安全创建适配器(
    工厂: 智能体工厂,
    模型: str,
    配置: dict[str, Any]
) -> Optional[智能体适配器]:
    """
    安全创建智能体适配器
    - 捕获所有异常，返回 None 而不是崩溃
    - 记录详细的错误日志
    - 用于优雅降级：一个智能体失败不影响其他智能体
    """
```

---

## 4. 类别路由系统

### 4.1 类别定义与含义

8 个类别按**任务复杂度和领域**划分：

| 类别 | 适用场景 | 示例任务 |
|------|---------|---------|
| **超级大脑** (`ultrabrain`) | 架构设计、高难度逻辑推理 | 系统架构设计、复杂算法设计 |
| **深度** (`deep`) | 深度代码生成、复杂实现 | 后端服务开发、复杂业务逻辑 |
| **快速** (`quick`) | 快速响应、简单任务 | 代码格式化、简单函数生成 |
| **视觉工程** (`visual-engineering`) | 前端、UI、视觉相关 | 前端页面开发、CSS 样式、交互设计 |
| **专家** (`specialist`) | 特定领域专长 | 代码审查、安全审计、性能优化 |
| **探索** (`exploration`) | 代码探索、需求分析 | 代码库分析、需求梳理 |
| **顾问** (`advisor`) | 咨询、审查、评估 | 技术方案评审、风险评估 |
| **工具** (`utility`) | 通用工具类 | 文档生成、数据转换 |

### 4.2 默认路由表

路由表定义在 `类别路由器.__init__()` 中，每个类别映射到按优先级排序的智能体 ID 列表：

```python
self.路由表: dict[智能体类别, list[str]] = {
    智能体类别.超级大脑: ["claude_code"],
    智能体类别.深度:     ["claude_code", "opencode"],
    智能体类别.快速:     ["claude_code", "opencode"],
    智能体类别.视觉工程: ["claude_code"],
    智能体类别.专家:     ["claude_code", "codex"],
    智能体类别.探索:     ["claude_code", "opencode"],
    智能体类别.顾问:     ["claude_code"],
    智能体类别.工具:     ["claude_code", "opencode", "codex"],
}
```

列表顺序代表**优先级**：第一个智能体最优先选择。如果高优先级智能体不可用，会尝试后续候选。

### 4.3 选择逻辑

`类别路由器.选择智能体()` 的完整选择流程：

```
1. 从路由表获取该类别的候选智能体 ID 列表
2. 依次从注册表获取智能体实例
3. 过滤：只保留健康的智能体（_是否健康()）
4. 对每个候选智能体进行多维评分（_评分智能体()）
5. 按评分降序排序
6. 返回评分最高的智能体
```

### 4.4 评分算法

评分维度与权重（`_评分智能体()` 方法）：

| 维度 | 权重/计算方式 | 说明 |
|------|-------------|------|
| 能力匹配度 | `+10 × 匹配数` | 任务需求的能力与智能体能力的交集大小 |
| 上下文窗口匹配 | `+20`（满足）或 `-差值/1000`（不足） | 智能体上下文窗口是否满足预估令牌数 |
| 成本 | `-平均成本/10` | 优先选择便宜的智能体 |
| 负载均衡 | `-负载×15` | 优先选择负载低的智能体 |
| 任务优先级 | `+优先级×5` | 高优先级任务给予额外加分 |

### 4.5 自定义路由

可通过 `注册类别路由()` 方法添加或修改类别路由：

```python
路由器 = 类别路由器()
路由器.设置注册表(注册表)

# 为"专家"类别添加新智能体
路由器.注册类别路由(
    类别=智能体类别.专家,
    智能体ID列表=["claude_code", "codex", "my_new_agent"]
)
```

---

## 5. 注册表与健康检查机制

### 5.1 智能体注册表

`智能体注册表` 管理所有可用智能体，提供注册、查询和初始化功能。

#### 注册方式

**方式一：注册工厂（推荐）**

```python
注册表 = 智能体注册表()
注册表.注册工厂(我的工厂())           # 注册工厂
注册表.设置配置("my_agent", {...})    # 设置配置
智能体 = 注册表.获取智能体("my_agent") # 首次获取时自动通过工厂创建
```

**方式二：直接注册实例**

```python
注册表 = 智能体注册表()
智能体 = MyAgentAdapter(模型="gpt-4", 配置={})
注册表.注册智能体(智能体)
```

#### 核心 API

| 方法 | 说明 |
|------|------|
| `注册工厂(工厂)` | 注册智能体工厂 |
| `注册智能体(智能体)` | 直接注册智能体实例 |
| `设置配置(智能体ID, 配置)` | 设置智能体配置 |
| `获取智能体(智能体ID)` | 获取智能体实例（优先返回已创建实例，否则从工厂创建） |
| `获取所有智能体ID()` | 获取所有已注册的智能体 ID |
| `获取所有健康智能体()` | 获取所有健康的智能体 |
| `初始化所有智能体()` | 异步初始化所有工厂注册的智能体 |
| `健康检查所有智能体()` | 异步对所有智能体执行健康检查 |
| `获取智能体数量()` | 获取已注册的智能体数量 |

#### 懒加载机制

`获取智能体()` 实现了懒加载：首次请求时才从工厂创建实例并缓存：

```python
def 获取智能体(self, 智能体ID: str) -> Optional[智能体适配器]:
    # 1. 先查已注册实例缓存
    if 智能体ID in self._已注册智能体:
        return self._已注册智能体[智能体ID]
    # 2. 再查工厂，使用安全创建
    if 智能体ID in self._智能体工厂:
        适配器 = 安全创建适配器(工厂, 模型, 配置)
        if 适配器:
            self._已注册智能体[智能体ID] = 适配器  # 缓存
            return 适配器
    return None
```

### 5.2 健康检查器

`健康检查器` 提供定期健康检查和负载统计功能。

#### 核心功能

| 方法 | 说明 |
|------|------|
| `注册智能体(智能体)` | 注册智能体用于健康检查 |
| `开始检查()` | 启动定期健康检查循环 |
| `停止检查()` | 停止健康检查 |
| `获取健康状态(智能体ID)` | 获取智能体当前健康状态 |
| `获取健康率(智能体ID, 时间窗口分钟)` | 获取指定时间窗口内的健康率 |
| `记录任务开始(智能体ID)` | 记录任务开始（增加并发数） |
| `记录任务完成(智能体ID, 成功, 响应时间毫秒)` | 记录任务完成 |
| `获取负载统计(智能体ID)` | 获取智能体负载统计 |
| `获取所有负载统计()` | 获取所有智能体负载统计 |
| `获取最低负载智能体(智能体ID列表)` | 从候选列表中选择负载最低的智能体 |

#### 健康检查记录

```python
@dataclass
class 健康检查记录:
    智能体ID: str
    状态: 智能体健康状态        # healthy / degraded / unhealthy
    检查时间: datetime
    响应时间毫秒: int = 0
    错误信息: str | None = None
```

#### 负载统计

```python
@dataclass
class 负载统计:
    智能体ID: str
    当前并发数: int = 0
    最大并发数: int = 5
    累计任务数: int = 0
    成功任务数: int = 0
    失败任务数: int = 0
    平均响应时间毫秒: int = 0
    最后任务时间: datetime | None = None

    @property
    def 负载率(self) -> float: ...    # 0.0-1.0

    @property
    def 成功率(self) -> float: ...    # 0.0-1.0
```

#### 工作流程

```
开始检查()
    │
    ▼
_检查循环() ── 每 30 秒执行一次 ──► _执行健康检查()
    │                                    │
    │                    对每个智能体调用 健康检查()
    │                    记录结果到 _健康记录
    │                    限制历史记录数为 100 条
    │
    ▼
停止检查() ── 取消异步任务
```

### 5.3 上下文管理器

`上下文管理器` 管理跨阶段的上下文传递和令牌预算分配。

#### 核心 API

| 方法 | 说明 |
|------|------|
| `创建阶段上下文(阶段ID, 输入数据)` | 创建新的阶段上下文 |
| `添加片段(阶段ID, 来源, 内容, 优先级, 是否必须)` | 添加上下文片段 |
| `获取优化上下文(阶段ID, 令牌预算)` | 根据令牌预算智能选择片段 |
| `记录制品(阶段ID, 制品)` | 记录阶段产出制品 |
| `记录中间结果(阶段ID, 键, 值)` | 记录中间结果 |
| `获取前序制品(当前阶段ID)` | 获取前序阶段的制品 |
| `压缩上下文(内容, 目标令牌数)` | 压缩上下文到目标令牌数 |
| `清理阶段(阶段ID)` | 清理阶段上下文 |

#### 令牌预算

```python
@dataclass
class 令牌预算:
    总预算: int = 200000
    已分配: int = 0

    @property
    def 剩余预算(self) -> int: ...

    @property
    def 使用率(self) -> float: ...

    def 分配(self, 数量: int) -> bool: ...   # 分配令牌
    def 释放(self, 数量: int): ...           # 释放令牌
    def 重置(self): ...                      # 重置预算
```

---

## 6. 现有适配器接口说明

### 6.1 Claude Code 适配器

**文件**：`src/hermes/智能体/适配器/claude_code.py`

| 属性 | 值 |
|------|-----|
| 智能体ID | `"claude_code"` |
| 类别 | `智能体类别.超级大脑` |
| 成本层级 | `智能体成本.昂贵` |
| 底层 SDK | `anthropic` (Anthropic Async API) |

**能力列表**：

| 能力名称 | 语言 | 上下文窗口 | 每千令牌成本 | 最大并发 |
|---------|------|----------|------------|---------|
| `code_generation` | python, javascript, typescript, java, go | 200,000 | $0.003 | 5 |
| `requirements_engineering` | markdown, json, yaml | 200,000 | $0.003 | 5 |
| `architecture_design` | markdown, diagrams | 200,000 | $0.003 | 5 |
| `code_review` | python, javascript, typescript, java, go | 200,000 | $0.003 | 5 |

**初始化配置**：

```python
{
    "api_key": "sk-ant-...",           # Anthropic API 密钥
    "max_tokens": 4096,                # 最大输出令牌数
    "模型": "claude-3-5-sonnet-20241022"  # 模型名称
}
```

**健康检查**：发送一条测试消息到 Claude API，检查响应是否正常。

**提示词构建**：使用 `提示词模板管理器` 根据任务类型选择模板，填充上下文变量。模板生成失败时回退到默认提示词。

**制品提取**：从输出文本中解析 Markdown 代码块（` ``` ` 格式），提取为代码制品。

**取消任务**：不支持，返回 `False`。

### 6.2 OpenCode 适配器

**文件**：`src/hermes/智能体/适配器/opencode.py`

| 属性 | 值 |
|------|-----|
| 智能体ID | `"opencode"` |
| 类别 | `智能体类别.深度` |
| 成本层级 | `智能体成本.便宜` |
| 底层实现 | CLI 子进程 (`asyncio.create_subprocess_exec`) |

**能力列表**：

| 能力名称 | 语言 | 上下文窗口 | 每千令牌成本 | 最大并发 |
|---------|------|----------|------------|---------|
| `code_generation` | python, javascript, typescript, go, rust | 128,000 | $0.001 | 3 |
| `code_review` | python, javascript, typescript, go, rust | 128,000 | $0.001 | 3 |
| `exploration` | python, javascript, typescript | 128,000 | $0.001 | 3 |

**初始化配置**：

```python
{
    "path": "opencode",     # OpenCode CLI 路径
    "timeout": 300,         # 执行超时（秒）
    "模型": "default"       # 模型名称
}
```

**健康检查**：执行 `opencode version` 命令，检查返回码是否为 0。

**执行方式**：通过 `asyncio.create_subprocess_exec` 启动子进程，传入 `--prompt` 参数。支持超时控制。

**流式执行**：启动带 `--stream` 参数的子进程，逐行读取 stdout。

**取消任务**：支持，通过 `process.terminate()` 终止子进程。

### 6.3 Codex 适配器

**文件**：`src/hermes/智能体/适配器/codex.py`

| 属性 | 值 |
|------|-----|
| 智能体ID | `"codex"` |
| 类别 | `智能体类别.专家` |
| 成本层级 | `智能体成本.便宜` |
| 底层 SDK | `openai` (OpenAI Async API) |

**能力列表**：

| 能力名称 | 语言 | 上下文窗口 | 每千令牌成本 | 最大并发 |
|---------|------|----------|------------|---------|
| `code_generation` | python, javascript, typescript, java, csharp | 16,000 | $0.0004 | 10 |
| `test_generation` | python, javascript, typescript | 16,000 | $0.0004 | 10 |
| `code_explanation` | python, javascript, typescript, java | 16,000 | $0.0004 | 10 |

**初始化配置**：

```python
{
    "api_key": "sk-...",           # OpenAI API 密钥
    "base_url": "https://...",     # API 基础 URL（可选）
    "max_tokens": 4096,            # 最大输出令牌数
    "temperature": 0.7,            # 温度参数
    "模型": "gpt-4"               # 模型名称
}
```

**健康检查**：发送一条测试消息到 OpenAI API，检查响应是否正常。

**执行方式**：通过 `openai.AsyncOpenAI` 客户端调用 Chat Completions API。

**流式执行**：使用 `stream=True` 参数，逐块 yield 增量内容。

**取消任务**：不支持，返回 `False`。

### 6.4 适配器对比总结

| 特性 | Claude Code | OpenCode | Codex |
|------|------------|----------|-------|
| 通信方式 | HTTP API | CLI 子进程 | HTTP API |
| 上下文窗口 | 200K | 128K | 16K |
| 最大并发 | 5 | 3 | 10 |
| 流式支持 | 是 | 是 | 是 |
| 取消任务 | 否 | 是 | 否 |
| 成本层级 | 昂贵 | 便宜 | 便宜 |
| 主要类别 | 超级大脑 | 深度 | 专家 |
| 独有能力 | 架构设计、需求工程 | 探索 | 代码解释 |

---

## 7. 新适配器接入完整示例

本节以创建一个 **Gemini 适配器** 为例，展示从零开始创建新智能体适配器的完整流程。

### 第一步：创建适配器文件

在 `src/hermes/智能体/适配器/` 目录下创建 `gemini.py`：

```python
"""Gemini适配器实现"""
import time
from typing import AsyncIterator, Any, Optional
import logging

from ..基础 import (
    智能体适配器,
    智能体能力,
    智能体类别,
    智能体成本,
    任务结果,
    上下文包
)

logger = logging.getLogger(__name__)


class Gemini适配器(智能体适配器):
    """
    Gemini适配器

    通过Google Gemini API执行任务
    专注于多模态和长上下文任务
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._客户端 = None

    @property
    def 智能体ID(self) -> str:
        return "gemini"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "java", "go"],
                上下文窗口=1000000,
                每千令牌成本=0.001,
                最大并发任务数=5
            ),
            智能体能力(
                名称="architecture_design",
                语言列表=["markdown", "diagrams"],
                上下文窗口=1000000,
                每千令牌成本=0.001,
                最大并发任务数=5
            ),
            智能体能力(
                名称="code_review",
                语言列表=["python", "javascript", "typescript", "java", "go"],
                上下文窗口=1000000,
                每千令牌成本=0.001,
                最大并发任务数=5
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.深度

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.便宜

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化Gemini API客户端"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=配置.get("api_key"))
            self._客户端 = genai.GenerativeModel(
                model_name=self._模型
            )
            logger.info(f"Gemini适配器初始化成功 (模型: {self._模型})")
        except ImportError:
            logger.error("未安装google-generativeai库，请运行: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"初始化Gemini API客户端失败: {e}")
            raise

    async def 健康检查(self) -> bool:
        """执行健康检查"""
        try:
            if not self._客户端:
                return False
            响应 = await self._客户端.generate_content_async("test")
            return True
        except Exception as e:
            logger.error(f"Gemini健康检查失败: {e}")
            return False

    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        """执行单个任务"""
        开始时间 = time.time()

        try:
            提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

            响应 = await self._客户端.generate_content_async(
                提示词,
                generation_config={
                    "max_output_tokens": self._配置.get("max_tokens", 4096),
                    "temperature": self._配置.get("temperature", 0.7),
                }
            )

            输出文本 = 响应.text
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)

            制品 = self._提取制品(输出文本, 任务类型)

            return 任务结果(
                任务ID=任务ID,
                状态="completed",
                输出数据={
                    "文本": 输出文本,
                    "任务类型": 任务类型,
                    "模型": self._模型
                },
                制品列表=制品,
                使用的令牌数=响应.usage_metadata.total_token_count,
                成本=self._计算成本(响应.usage_metadata),
                耗时毫秒=耗时毫秒,
                错误=None
            )

        except Exception as e:
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)
            logger.error(f"任务 {任务ID} 执行失败: {e}", exc_info=True)

            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时毫秒,
                错误=str(e)
            )

    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行任务"""
        提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

        响应 = await self._客户端.generate_content_async(
            提示词,
            generation_config={
                "max_output_tokens": self._配置.get("max_tokens", 4096),
            },
            stream=True
        )

        async for 块 in 响应:
            if 块.text:
                yield {"type": "text", "text": 块.text}

        yield {"type": "done", "任务ID": 任务ID}

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        logger.warning(f"Gemini适配器不支持取消任务 {任务ID}")
        return False

    def _构建提示词(self, 任务类型: str, 输入数据: dict[str, Any], 上下文: 上下文包) -> str:
        """构建提示词"""
        from ..提示词模板 import 提示词模板管理器

        模板管理器 = 提示词模板管理器()
        模板名称 = 模板管理器.根据任务类型获取模板(任务类型)

        上下文数据 = {
            "需求描述": 输入数据.get("需求", 输入数据.get("description", "")),
            "代码内容": 输入数据.get("代码", 输入数据.get("code", "")),
            "代码语言": 输入数据.get("语言", 输入数据.get("language", "python")),
            "项目上下文": str(上下文.元数据) if 上下文 and 上下文.元数据 else "",
        }

        提示词结果 = 模板管理器.生成提示词(模板名称, 上下文数据)
        if 提示词结果:
            return 提示词结果["用户提示词"]

        部分 = ["你是一个专业的软件开发助手。"]
        if 输入数据:
            部分.append("\n## 输入数据\n")
            for 键, 值 in 输入数据.items():
                部分.append(f"**{键}**: {值}")
        return "\n".join(部分)

    def _计算成本(self, 使用量) -> float:
        """计算API调用成本"""
        总令牌 = 使用量.total_token_count or 0
        return 总令牌 * 0.001 / 1000

    def _提取制品(self, 输出文本: str, 任务类型: str) -> list[dict]:
        """从输出中提取制品"""
        制品 = []
        if "```" in 输出文本:
            代码块 = []
            在代码块中 = False
            for 行 in 输出文本.split("\n"):
                if 行.startswith("```"):
                    在代码块中 = not 在代码块中
                    if not 在代码块中 and 代码块:
                        制品.append({
                            "类型": "code",
                            "内容": "\n".join(代码块),
                            "语言": "unknown"
                        })
                        代码块 = []
                elif 在代码块中:
                    代码块.append(行)
        return 制品
```

### 第二步：创建工厂类

在同一文件中添加工厂类：

```python
class Gemini工厂(智能体工厂):
    """Gemini智能体工厂"""

    @property
    def 智能体ID(self) -> str:
        return "gemini"

    def 创建(self, 模型: str, 配置: dict[str, Any]) -> 智能体适配器:
        return Gemini适配器(模型=模型, 配置=配置)
```

### 第三步：更新适配器模块导出

编辑 `src/hermes/智能体/适配器/__init__.py`：

```python
"""智能体适配器"""
from .claude_code import ClaudeCode适配器
from .opencode import OpenCode适配器
from .codex import Codex适配器
from .gemini import Gemini适配器, Gemini工厂

__all__ = [
    "ClaudeCode适配器",
    "OpenCode适配器",
    "Codex适配器",
    "Gemini适配器",
    "Gemini工厂",
]
```

### 第四步：注册到路由表

更新 `src/hermes/智能体/类别.py` 中的路由表，将 Gemini 加入合适的类别：

```python
self.路由表: dict[智能体类别, list[str]] = {
    智能体类别.超级大脑: ["claude_code", "gemini"],     # 新增
    智能体类别.深度:     ["claude_code", "opencode", "gemini"],  # 新增
    智能体类别.快速:     ["claude_code", "opencode"],
    智能体类别.视觉工程: ["claude_code", "gemini"],     # 新增（多模态优势）
    智能体类别.专家:     ["claude_code", "codex"],
    智能体类别.探索:     ["claude_code", "opencode"],
    智能体类别.顾问:     ["claude_code", "gemini"],     # 新增
    智能体类别.工具:     ["claude_code", "opencode", "codex", "gemini"],  # 新增
}
```

### 第五步：注册到智能体注册表

在应用初始化代码中注册工厂和配置：

```python
from hermes.智能体 import 智能体注册表, 类别路由器
from hermes.智能体.适配器 import Gemini工厂

# 创建注册表和路由器
注册表 = 智能体注册表()
路由器 = 类别路由器()

# 注册 Gemini 工厂
注册表.注册工厂(Gemini工厂())

# 配置 Gemini
注册表.设置配置("gemini", {
    "api_key": "AIza...",
    "模型": "gemini-1.5-pro",
    "max_tokens": 4096,
    "temperature": 0.7
})

# 设置路由器
路由器.设置注册表(注册表)

# 初始化所有智能体
await 注册表.初始化所有智能体()
```

### 第六步：通过配置文件集成

在项目配置 JSONC 文件中添加 Gemini 配置：

```jsonc
{
    "智能体": {
        "gemini": {
            "api_key": "AIza...",
            "模型": "gemini-1.5-pro",
            "最大令牌数": 4096,
            "温度": 0.7
        }
    },
    "类别": {
        "ultrabrain": {
            "描述": "架构级，高难度逻辑",
            "智能体优先级": ["claude_code", "gemini"]
        },
        "deep": {
            "描述": "深度代码生成，复杂实现",
            "智能体优先级": ["claude_code", "opencode", "gemini"]
        }
    }
}
```

### 第七步：在流水线中使用

在流水线定义中指定类别，路由器会自动选择 Gemini：

```json
{
    "name": "全栈开发",
    "stages": [
        {
            "id": "design",
            "name": "架构设计",
            "type": "sequential",
            "tasks": [
                {
                    "id": "arch",
                    "name": "设计架构",
                    "type": "architecture_design",
                    "category": "ultrabrain"
                }
            ]
        },
        {
            "id": "dev",
            "name": "开发实现",
            "type": "parallel",
            "tasks": [
                {
                    "id": "backend",
                    "name": "后端开发",
                    "type": "code_generation",
                    "category": "deep"
                }
            ]
        }
    ]
}
```

### 接入检查清单

完成新适配器接入后，请逐项确认：

- [ ] 适配器类继承 `智能体适配器` 并实现所有抽象成员
- [ ] `智能体ID` 属性返回唯一标识字符串
- [ ] `能力列表` 正确声明了所有能力及其参数
- [ ] `类别` 属性返回合适的 `智能体类别` 枚举值
- [ ] `成本层级` 属性返回正确的成本层级
- [ ] `初始化()` 方法正确处理 SDK 导入失败和配置错误
- [ ] `健康检查()` 方法能可靠检测智能体可用性
- [ ] `执行任务()` 在成功和失败时都返回 `任务结果`（不抛异常）
- [ ] `流式执行任务()` 正确 yield 增量结果字典
- [ ] `取消任务()` 返回正确的布尔值
- [ ] 工厂类继承 `智能体工厂` 并实现 `创建()` 方法
- [ ] 适配器已添加到 `适配器/__init__.py` 的导出
- [ ] 路由表已更新，新智能体已加入合适类别
- [ ] 注册表已注册工厂和配置
- [ ] 配置文件已添加新智能体的配置项

---

## 附录：提示词模板系统

适配器可通过 `提示词模板管理器` 生成标准化提示词，而非硬编码提示词字符串。

### 内置模板

| 模板名称 | 对应任务类型 | 说明 |
|---------|------------|------|
| 代码生成 | `code_generation` | 根据需求生成代码 |
| 代码审查 | `code_review` | 审查代码质量、安全性和性能 |
| 测试生成 | `test_generation` | 为代码生成测试用例 |
| 文档生成 | `documentation` | 生成代码文档和 API 文档 |
| 架构设计 | `architecture` | 设计系统架构和技术方案 |
| 需求分析 | `requirements` | 分析和理解项目需求 |

### 使用方式

```python
from hermes.智能体.提示词模板 import 提示词模板管理器

模板管理器 = 提示词模板管理器()

# 根据任务类型获取模板名称
模板名称 = 模板管理器.根据任务类型获取模板("code_generation")  # → "代码生成"

# 生成提示词
结果 = 模板管理器.生成提示词("代码生成", {
    "需求描述": "实现用户登录接口",
    "项目上下文": "FastAPI项目",
    "代码语言": "python"
})
# 结果 = {"系统提示词": "...", "用户提示词": "..."}

# 获取所有可用模板
所有模板 = 模板管理器.获取所有模板()
```

### 任务类型到模板的映射

```python
映射 = {
    "code_generation": "代码生成",
    "code_review": "代码审查",
    "test_generation": "测试生成",
    "documentation": "文档生成",
    "architecture": "架构设计",
    "requirements": "需求分析",
}
```

未匹配的任务类型默认使用"代码生成"模板。
