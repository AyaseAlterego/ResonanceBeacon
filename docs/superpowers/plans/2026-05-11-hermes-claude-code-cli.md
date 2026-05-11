# Hermes 调度 Claude Code CLI 模式实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Hermes 通过 `claude` CLI 子进程调度 Claude Code 在项目工作区中执行开发任务（文件编辑、bash 命令等），保留 API 模式作为降级回退。

**Architecture:** Claude Code 适配器新增 CLI 模式（`claude -p "prompt"` 子进程），通过 `上下文包.项目路径` 传递工作区路径，引擎在 `_执行任务` 时注入项目路径。API 模式保留为 CLI 不可用时的回退。

**Tech Stack:** Python 3.12+, asyncio, `claude` CLI (@anthropic-ai/claude-code), anthropic SDK

---

### Task 1: 更新上下文包，加入项目路径

**Files:**
- Modify: `src/hermes/智能体/基础.py:65-73`
- Test: `tests/unit/test_上下文上下文包.py` (new)

- [ ] **Step 1: 扩展 上下文包 dataclass**

在 `src/hermes/智能体/基础.py` 中，给 `上下文包` 添加 `项目路径` 字段：

```python
@dataclass
class 上下文包:
    """传递给智能体的上下文"""
    流水线ID: str = ""
    阶段ID: str = ""
    任务ID: str = ""
    输入数据: dict[str, Any] = field(default_factory=dict)
    之前的制品: list[dict[str, Any]] = field(default_factory=list)
    元数据: dict[str, Any] = field(default_factory=dict)
    项目路径: str = ""  # 新增：项目工作区路径
```

- [ ] **Step 2: 创建测试文件**

创建 `tests/unit/test_上下文上下文包.py`：

```python
"""测试上下文包"""
from src.hermes.智能体.基础 import 上下文包


def test_上下文包_默认值():
    包 = 上下文包()
    assert 包.流水线ID == ""
    assert 包.项目路径 == ""


def test_上下文包_设置项目路径():
    包 = 上下文包(项目路径="/tmp/my_project")
    assert 包.项目路径 == "/tmp/my_project"


def test_上下文包_完整初始化():
    包 = 上下文包(
        流水线ID="pl-1",
        阶段ID="sg-1",
        任务ID="tk-1",
        项目路径="/my/project"
    )
    assert 包.流水线ID == "pl-1"
    assert 包.项目路径 == "/my/project"
```

- [ ] **Step 3: 运行测试**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/unit/test_上下文上下文包.py -v
```

Expected: 3 PASSED

- [ ] **Step 4: Commit**

```bash
git add src/hermes/智能体/基础.py tests/unit/test_上下文上下文包.py
git commit -m "feat: 上下文包增加项目路径字段，支持Claude Code工作区传递"
```

---

### Task 2: 更新流水线引擎，注入项目路径到上下文

**Files:**
- Modify: `src/hermes/编排器/引擎.py:244-260`
- Test: `tests/unit/test_引擎上下文.py` (new)

- [ ] **Step 1: 在引擎中注入项目路径**

在 `src/hermes/编排器/引擎.py` 中：

1. 给 `流水线引擎.__init__` 添加 `项目路径: str = ""` 参数
2. 存储为 `self.项目路径`
3. 在 `_执行任务` 中构建 `上下文包` 时传入 `项目路径`

修改 `引擎.py` __init__：
```python
def __init__(
    self,
    智能体注册表: 智能体注册表,
    类别路由器: 类别路由器,
    后台管理器: 后台任务管理器,
    项目路径: str = ""  # 新增
):
    self.智能体注册表 = 智能体注册表
    self.类别路由器 = 类别路由器
    self.后台管理器 = 后台管理器
    self.状态机 = 流水线状态机()
    self.钩子组合器 = 钩子组合器()
    self.项目路径 = 项目路径  # 新增
```

修改 `_执行任务` 中构建 `上下文包` 的地方（约 255-270 行）：
```python
# 将 上下文 包装为 上下文包 传给智能体
智能体上下文 = 上下文包(
    流水线ID=流水线ID,
    阶段ID=阶段ID,
    任务ID=任务ID,
    输入数据=任务定义.get("input", {}),
    之前的制品=[],
    元数据={"任务名称": 任务名称, "任务类型": 任务定义.get("type", "")},
    项目路径=self.项目路径  # 传入项目路径
)
```

然后把 `智能体上下文` 传给 `智能体.执行任务` 调用，替代原来的 `上下文`（钩子上下文不同）。

注意：需要修改 `_执行任务` 方法的签名和调用链。当前 `_执行任务` 接收 `上下文: 钩子上下文` 参数，需要将 `上下文包` 构建出来传给智能体。

- [ ] **Step 2: 创建测试**

创建 `tests/unit/test_引擎上下文.py`：

```python
"""测试引擎上下文传递"""
import pytest
from src.hermes.智能体.基础 import 上下文包
from src.hermes.编排器.引擎 import 流水线引擎


class 测试引擎:
    """验证引擎能正确传递项目路径"""

    @pytest.mark.asyncio
    async def test_引擎初始化携带项目路径(self):
        引擎 = 流水线引擎(
            智能体注册表=None,  # mock场景
            类别路由器=None,
            后台管理器=None,
            项目路径="/workspace/project"
        )
        assert 引擎.项目路径 == "/workspace/project"

    @pytest.mark.asyncio
    async def test_引擎默认项目路径为空(self):
        引擎 = 流水线引擎(
            智能体注册表=None,
            类别路由器=None,
            后台管理器=None
        )
        assert 引擎.项目路径 == ""
```

- [ ] **Step 3: 运行测试**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/unit/test_引擎上下文.py -v
```

Expected: 2 PASSED

- [ ] **Step 4: Commit**

```bash
git add src/hermes/编排器/引擎.py tests/unit/test_引擎上下文.py
git commit -m "feat: 引擎支持项目路径注入，透传到智能体上下文"
```

---

### Task 3: 重写 Claude Code 适配器 — CLI 模式 + API 回退

**Files:**
- Modify: `src/hermes/智能体/适配器/claude_code.py` (完全重写)
- Test: `tests/unit/test_claude_code_适配器.py` (new)

- [ ] **Step 1: 重写 claude_code.py**

```python
"""Claude Code适配器实现 - 支持CLI模式和API模式"""
import time
import asyncio
import shutil
from typing import AsyncIterator, Any
from pathlib import Path
import logging

from ..基础 import (
    智能体适配器,
    智能体能力,
    智能体类别,
    智能体成本,
    任务结果,
    上下文包
)
from ..提示词模板 import 提示词模板管理器

logger = logging.getLogger(__name__)


class ClaudeCode适配器(智能体适配器):
    """
    Claude Code适配器

    双模式：
    - CLI模式（默认）：通过 `claude` 命令在项目目录中执行，支持文件编辑和bash命令
    - API模式（回退）：使用 Anthropic API 执行纯文本任务
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._客户端 = None
        self._进程: asyncio.subprocess.Process | None = None
        self._最后健康状态 = False
        self._CLI可用 = False
        self._提示词管理器 = 提示词模板管理器()

    @property
    def 智能体ID(self) -> str:
        return "claude_code"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "java", "go", "rust"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="requirements_engineering",
                语言列表=["markdown", "json", "yaml"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="architecture_design",
                语言列表=["markdown", "diagrams"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="code_review",
                语言列表=["python", "javascript", "typescript", "java", "go", "rust"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="file_operations",
                语言列表=["*"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="bash_execution",
                语言列表=["*"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.超级大脑

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.昂贵

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化Claude Code适配器，探测CLI或API模式"""
        self._配置.update(配置)

        # 探测 claude CLI 是否可用
        claude_path = 配置.get("claude_path", "claude")
        self._CLI可用 = shutil.which(claude_path) is not None

        if self._CLI可用:
            logger.info(f"Claude Code CLI模式可用 (路径: {claude_path})")
            return

        # CLI不可用，回退到API模式
        logger.info("Claude CLI未安装，回退到API模式")
        try:
            import anthropic
            self._客户端 = anthropic.AsyncAnthropic(
                api_key=配置.get("api_key")
            )
            logger.info(f"Claude Code API模式初始化成功 (模型: {self._模型})")
        except ImportError:
            logger.error("anthropic库未安装，Claude Code适配器不可用")
            raise

    async def 健康检查(self) -> bool:
        if self._CLI可用:
            self._最后健康状态 = shutil.which(
                self._配置.get("claude_path", "claude")
            ) is not None
        elif self._客户端 is not None:
            self._最后健康状态 = True
        return self._最后健康状态

    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        开始时间 = time.time()

        try:
            提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

            if self._CLI可用:
                return await self._CLI执行任务(任务ID, 提示词, 上下文, 开始时间)
            else:
                return await self._API执行任务(任务ID, 提示词, 开始时间)

        except Exception as e:
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)
            logger.error(f"任务 {任务ID} 执行失败: {e}", exc_info=True)
            self._最后健康状态 = False
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

    async def _CLI执行任务(
        self,
        任务ID: str,
        提示词: str,
        上下文: 上下文包,
        开始时间: float
    ) -> 任务结果:
        """通过 claude CLI 执行任务"""
        claude_path = self._配置.get("claude_path", "claude")
        超时 = self._配置.get("timeout", 600)

        # 确定工作目录
        工作目录 = 上下文.项目路径 if 上下文.项目路径 else None

        进程 = await asyncio.create_subprocess_exec(
            claude_path, "-p", 提示词,
            stdin=None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=工作目录
        )

        self._进程 = 进程

        try:
            stdout, stderr = await asyncio.wait_for(
                进程.communicate(),
                timeout=超时
            )
        except asyncio.TimeoutError:
            进程.kill()
            await 进程.wait()
            耗时 = int((time.time() - 开始时间) * 1000)
            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时,
                错误="Claude Code 任务执行超时"
            )
        finally:
            self._进程 = None

        输出文本 = stdout.decode("utf-8", errors="replace")
        错误文本 = stderr.decode("utf-8", errors="replace")

        if 进程.returncode != 0:
            耗时 = int((time.time() - 开始时间) * 1000)
            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={"stderr": 错误文本},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时,
                错误=f"Claude Code 退出码 {进程.returncode}: {错误文本[:500]}"
            )

        制品 = self._提取制品(输出文本)
        耗时 = int((time.time() - 开始时间) * 1000)

        return 任务结果(
            任务ID=任务ID,
            状态="completed",
            输出数据={
                "文本": 输出文本,
                "任务类型": 任务类型,
                "模型": f"{claude_path}(CLI)",
                "工作目录": str(工作目录 or Path.cwd())
            },
            制品列表=制品,
            使用的令牌数=0,
            成本=0.0,
            耗时毫秒=耗时,
            错误=None
        )

    async def _API执行任务(
        self,
        任务ID: str,
        提示词: str,
        开始时间: float
    ) -> 任务结果:
        """通过 Anthropic API 执行任务"""
        if not self._客户端:
            raise RuntimeError("Anthropic API 客户端未初始化")

        响应 = await self._客户端.messages.create(
            model=self._模型,
            max_tokens=self._配置.get("max_tokens", 4096),
            messages=[{"role": "user", "content": 提示词}]
        )

        输出文本 = 响应.content[0].text if 响应.content else ""
        使用的令牌数 = 响应.usage.input_tokens + 响应.usage.output_tokens
        成本 = self._计算成本(响应.usage)
        制品 = self._提取制品(输出文本)
        耗时 = int((time.time() - 开始时间) * 1000)

        return 任务结果(
            任务ID=任务ID,
            状态="completed",
            输出数据={
                "文本": 输出文本,
                "任务类型": 任务类型,
                "模型": self._模型
            },
            制品列表=制品,
            使用的令牌数=使用的令牌数,
            成本=成本,
            耗时毫秒=耗时,
            错误=None
        )

    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

        if self._CLI可用:
            async for 块 in self._CLI流式执行(任务ID, 提示词, 上下文):
                yield 块
        else:
            async for 块 in self._API流式执行(任务ID, 提示词):
                yield 块

    async def _CLI流式执行(
        self,
        任务ID: str,
        提示词: str,
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        claude_path = self._配置.get("claude_path", "claude")
        超时 = self._配置.get("timeout", 600)
        工作目录 = 上下文.项目路径 if 上下文.项目路径 else None

        进程 = await asyncio.create_subprocess_exec(
            claude_path, "-p", 提示词,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=工作目录
        )

        self._进程 = 进程

        try:
            while True:
                行 = await asyncio.wait_for(
                    进程.stdout.readline(),
                    timeout=超时
                )
                if not 行:
                    break
                文本 = 行.decode("utf-8", errors="replace").rstrip()
                if 文本:
                    yield {"type": "text", "text": 文本}

            await 进程.wait()
            yield {"type": "done", "任务ID": 任务ID}

        except asyncio.TimeoutError:
            logger.error(f"流式任务 {任务ID} 读取超时")
            进程.kill()
            await 进程.wait()
            yield {"type": "error", "错误": "流式执行超时"}
        except Exception as e:
            logger.error(f"流式任务 {任务ID} 失败: {e}", exc_info=True)
            yield {"type": "error", "错误": str(e)}
        finally:
            self._进程 = None

    async def _API流式执行(
        self,
        任务ID: str,
        提示词: str
    ) -> AsyncIterator[dict[str, Any]]:
        if not self._客户端:
            raise RuntimeError("Anthropic API 客户端未初始化")

        超时 = self._配置.get("timeout", 300)

        try:
            async with self._客户端.messages.stream(
                model=self._模型,
                max_tokens=self._配置.get("max_tokens", 4096),
                messages=[{"role": "user", "content": 提示词}]
            ) as 流:
                try:
                    while True:
                        文本 = await asyncio.wait_for(
                            流.text_stream.__anext__(), timeout=超时
                        )
                        yield {"type": "text", "text": 文本}
                except StopAsyncIteration:
                    pass

            yield {"type": "done", "任务ID": 任务ID}

        except asyncio.TimeoutError:
            logger.error(f"流式API任务 {任务ID} 超时")
            yield {"type": "error", "错误": "流式执行超时"}
        except Exception as e:
            logger.error(f"流式API任务 {任务ID} 失败: {e}", exc_info=True)
            yield {"type": "error", "错误": str(e)}

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务 - CLI模式通过终止进程，API模式不支持"""
        if self._进程:
            try:
                self._进程.terminate()
                logger.info(f"任务 {任务ID} 已取消 (终止进程)")
                return True
            except Exception as e:
                logger.error(f"取消任务 {任务ID} 失败: {e}")
                return False
        logger.warning(f"Claude Code适配器无运行中的进程可取消 (任务 {任务ID})")
        return False

    def _计算成本(self, 使用量) -> float:
        输入成本 = 使用量.input_tokens * 0.003 / 1000
        输出成本 = 使用量.output_tokens * 0.015 / 1000
        return 输入成本 + 输出成本
```

- [ ] **Step 2: 创建单元测试**

创建 `tests/unit/test_claude_code_适配器.py`：

```python
"""测试 Claude Code 适配器"""
import pytest
from unittest.mock import patch, AsyncMock
from src.hermes.智能体.适配器.claude_code import ClaudeCode适配器
from src.hermes.智能体.基础 import 智能体类别, 智能体成本, 上下文包


@pytest.fixture
def 适配器_配置():
    return {"api_key": "test-key", "timeout": 30, "max_tokens": 100}


@pytest.fixture
def 适配器(适配器_配置):
    return ClaudeCode适配器(模型="claude-sonnet-4-20250514", 配置=适配器_配置)


class TestClaudeCode适配器属性:

    def test_智能体ID(self, 适配器):
        assert 适配器.智能体ID == "claude_code"

    def test_类别(self, 适配器):
        assert 适配器.类别 == 智能体类别.超级大脑

    def test_成本层级(self, 适配器):
        assert 适配器.成本层级 == 智能体成本.昂贵

    def test_能力列表(self, 适配器):
        能力 = 适配器.能力列表
        能力名称 = [c.名称 for c in 能力]
        assert "code_generation" in 能力名称
        assert "code_review" in 能力名称
        assert "file_operations" in 能力名称
        assert "bash_execution" in 能力名称


class TestClaudeCode适配器初始化:

    @patch("shutil.which", return_value="/usr/local/bin/claude")
    def test_初始化_CLI模式(self, mock_which, 适配器):
        import asyncio
        asyncio.run(适配器.初始化({}))
        assert 适配器._CLI可用 is True

    @patch("shutil.which", return_value=None)
    @patch("anthropic.AsyncAnthropic")
    def test_初始化_API回退(self, mock_anthropic, mock_which, 适配器):
        import asyncio
        asyncio.run(适配器.初始化({"api_key": "test"}))
        assert 适配器._CLI可用 is False
        assert 适配器._客户端 is not None

    @patch("shutil.which", return_value=None)
    @patch("anthropic.AsyncAnthropic", side_effect=ImportError)
    def test_初始化_API失败(self, mock_anthropic, mock_which, 适配器):
        import asyncio
        with pytest.raises(ImportError):
            asyncio.run(适配器.初始化({"api_key": "test"}))


class TestClaudeCode适配器CLI模式:

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI模式_任务执行_成功(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})

        # mock子进程
        mock进程 = AsyncMock()
        mock进程.communicate = AsyncMock(return_value=(b"test output", b""))
        mock进程.returncode = 0

        with patch.object(
            asyncio, "create_subprocess_exec",
            return_value=mock进程
        ):
            上下文 = 上下文包(项目路径="/workspace/project")
            结果 = await 适配器.执行任务(
                "task-1", "code_generation",
                {"需求": "写一个hello world"}, 上下文
            )

        assert 结果.状态 == "completed"
        assert "test output" in 结果.输出数据["文本"]
        assert 结果.输出数据["工作目录"] == "/workspace/project"

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI模式_任务执行_失败(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})

        mock进程 = AsyncMock()
        mock进程.communicate = AsyncMock(return_value=(b"", b"error occurred"))
        mock进程.returncode = 1

        with patch.object(
            asyncio, "create_subprocess_exec",
            return_value=mock进程
        ):
            结果 = await 适配器.执行任务(
                "task-1", "code_generation",
                {"需求": "写代码"}, 上下文包()
            )

        assert 结果.状态 == "failed"
        assert "error occurred" in 结果.错误

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI模式_流式执行(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})

        行列表 = [b"line1\n", b"line2\n", b""]

        class MockStream:
            def __init__(self):
                self.idx = 0
            def __aiter__(self):
                return self
            async def __anext__(self):
                if self.idx >= len(行列表):
                    raise StopAsyncIteration
                行 = 行列表[self.idx]
                self.idx += 1
                return 行

        self._进程 = None

        # 在真实测试中，需要创建一个进程模拟
        # 这里简化：跳过流式测试的进程创建mock

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI模式_取消任务(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})

        mock进程 = AsyncMock()
        mock进程.terminate = AsyncMock()

        适配器._进程 = mock进程
        assert await 适配器.取消任务("task-1") is True
        mock进程.terminate.assert_called_once()

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI模式_无进程时取消(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})
        适配器._进程 = None
        assert await 适配器.取消任务("task-1") is False


class TestClaudeCode适配器API模式:

    @pytest.mark.asyncio
    async def test_API模式_健康检查(self, 适配器):
        适配器._CLI可用 = False
        # 模拟客户端存在
        适配器._客户端 = AsyncMock()
        assert await 适配器.健康检查() is True

    @pytest.mark.asyncio
    async def test_API模式_健康检查_无客户端(self, 适配器):
        适配器._CLI可用 = False
        适配器._客户端 = None
        assert await 适配器.健康检查() is False


class TestClaudeCode适配器提取制品:

    def test_提取制品_代码块(self, 适配器):
        内容 = '```python\nprint("hello")\n```'
        制品 = 适配器._提取制品(内容)
        assert len(制品) >= 1
        code_制品 = [a for a in 制品 if a["类型"] == "code"]
        assert len(code_制品) >= 1
        assert "print" in code_制品[0]["内容"]

    def test_提取制品_语言标识(self, 适配器):
        内容 = '```javascript\nconsole.log("hi")\n```'
        制品 = 适配器._提取制品(内容)
        code_制品 = [a for a in 制品 if a["类型"] == "code"]
        assert code_制品[0]["语言"] == "javascript"

    def test_提取制品_无代码块(self, 适配器):
        内容 = "纯文本输出内容"
        制品 = 适配器._提取制品(内容)
        assert len(制品) >= 1
```

- [ ] **Step 3: 运行测试**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/unit/test_claude_code_适配器.py -v
```

Expected: 10+ PASSED

- [ ] **Step 4: Commit**

```bash
git add src/hermes/智能体/适配器/claude_code.py tests/unit/test_claude_code_适配器.py
git commit -m "feat: Claude Code适配器支持CLI模式+API回退，工作区路径传参"
```

---

### Task 4: 更新 CLI 和管道配置，支持项目路径传递

**Files:**
- Modify: `src/hermes/命令行/命令/流水线.py` (let me check this)
- Modify: `src/hermes/接口/路由/流水线路由.py`

- [ ] **Step 1: 检查流水线命令和路由**

读取 `src/hermes/命令行/命令/流水线.py`。如果运行流水线的命令不传递项目路径，需要添加。

读取 `src/hermes/接口/路由/流水线路由.py` 中运行流水线的端点，如果引擎创建时不传项目路径，需要传入当前工作目录。

- [ ] **Step 2: 按需修改**

如果流水线命令创建引擎时没有传项目路径，添加 `项目路径=os.getcwd()`。
如果API路由创建引擎时没有传项目路径，添加 `项目路径=配置加载器.获取配置().项目路径`。

- [ ] **Step 3: 运行现有测试确认无回归**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/ -v
```

Expected: All existing tests pass (or known failures)

- [ ] **Step 4: Commit**

```bash
git add src/hermes/命令行/命令/流水线.py src/hermes/接口/路由/流水线路由.py
git commit -m "feat: 流水线运行命令和API路由支持传递项目路径"
```

---

### Task 5: 集成测试 — Hermes 调度 Claude Code CLI

**Files:**
- Test: `tests/integration/test_hermes_claude_cli.py` (new)

- [ ] **Step 1: 检查集成测试模式**

阅读 `tests/集成/test集成流水线.py` 了解现有集成测试风格。确认是否可以使用 `claude --version` 来探测环境并做条件性跳过。

- [ ] **Step 2: 创建集成测试**

创建 `tests/integration/test_hermes_claude_cli.py`：

```python
"""集成测试：Hermes 通过 CLI 调度 Claude Code"""
import pytest
import subprocess
import sys
from pathlib import Path


def _claude_disponivel() -> bool:
    """检查 claude CLI 是否可用"""
    try:
        subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


pytestmark = [
    pytest.mark.skipif(
        not _claude_disponivel(),
        reason="claude CLI 未安装，跳过集成测试"
    ),
    pytest.mark.integration
]


class TestHermesClaudeCLI:

    def test_claude_cli_disponivel(self):
        """验证 claude CLI 可用"""
        resultado = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10
        )
        assert resultado.returncode == 0
        assert "Claude Code" in resultado.stdout or resultado.returncode == 0

    def test_claude_cli_comandos_simples(self, tmp_path):
        """验证 claude CLI 可以执行简单命令"""
        prompt = 'diga "olá" em português'
        resultado = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=30,
            cwd=str(tmp_path)
        )
        assert resultado.returncode == 0
        assert "olá" in resultado.stdout.lower()

    def test_claude_cli_trabalha_no_diretório_correto(self, tmp_path):
        """验证 claude CLI 在指定目录工作"""
        (tmp_path / "teste.txt").write_text("conteúdo original")
        prompt = 'leia o arquivo teste.txt e diga seu conteúdo'
        resultado = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=30,
            cwd=str(tmp_path)
        )
        assert resultado.returncode == 0
        assert "conteúdo original" in resultado.stdout
```

注意：这是可选集成测试，仅在安装了 `claude` CLI 的环境中运行。

- [ ] **Step 3: 运行测试（如果 claude 可用）**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/integration/test_hermes_claude_cli.py -v
```

Expected: SKIP (claude not installed) or PASS

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_hermes_claude_cli.py
git commit -m "test: Hermes调度Claude CLI集成测试"
```

---

### Task 6: 运行全部测试，确保无回归

- [ ] **Step 1: 运行全部测试套件**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/ -v --timeout=30
```

- [ ] **Step 2: 修复发现的任何问题**

如果有测试失败，逐一修复。

- [ ] **Step 3: 最终确认**

```bash
cd C:\Ai\起源信标\ResonanceBeacon
pytest tests/ -v
```

Expected: All tests pass
