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
            智能体能力(名称="code_generation", 语言列表=["python", "javascript", "typescript", "java", "go", "rust"], 上下文窗口=200000, 每千令牌成本=0.003, 最大并发任务数=5),
            智能体能力(名称="requirements_engineering", 语言列表=["markdown", "json", "yaml"], 上下文窗口=200000, 每千令牌成本=0.003, 最大并发任务数=5),
            智能体能力(名称="architecture_design", 语言列表=["markdown", "diagrams"], 上下文窗口=200000, 每千令牌成本=0.003, 最大并发任务数=5),
            智能体能力(名称="code_review", 语言列表=["python", "javascript", "typescript", "java", "go", "rust"], 上下文窗口=200000, 每千令牌成本=0.003, 最大并发任务数=5),
            智能体能力(名称="file_operations", 语言列表=["*"], 上下文窗口=200000, 每千令牌成本=0.003, 最大并发任务数=5),
            智能体能力(名称="bash_execution", 语言列表=["*"], 上下文窗口=200000, 每千令牌成本=0.003, 最大并发任务数=5),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.超级大脑

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.昂贵

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        self._配置.update(配置)
        claude_path = 配置.get("claude_path", "claude")
        self._CLI可用 = shutil.which(claude_path) is not None
        if self._CLI可用:
            logger.info(f"Claude Code CLI模式可用 (路径: {claude_path})")
            return
        logger.info("Claude CLI未安装，回退到API模式")
        try:
            import anthropic
            self._客户端 = anthropic.AsyncAnthropic(api_key=配置.get("api_key"))
            logger.info(f"Claude Code API模式初始化成功 (模型: {self._模型})")
        except ImportError:
            logger.error("anthropic库未安装，Claude Code适配器不可用")
            raise

    async def 健康检查(self) -> bool:
        if self._CLI可用:
            self._最后健康状态 = shutil.which(self._配置.get("claude_path", "claude")) is not None
        elif self._客户端 is not None:
            self._最后健康状态 = True
        return self._最后健康状态

    async def 执行任务(self, 任务ID: str, 任务类型: str, 输入数据: dict[str, Any], 上下文: 上下文包) -> 任务结果:
        开始时间 = time.time()
        try:
            提示词 = self._构建提示词(任务类型, 输入数据, 上下文)
            if self._CLI可用:
                return await self._CLI执行任务(任务ID, 任务类型, 提示词, 上下文, 开始时间)
            else:
                return await self._API执行任务(任务ID, 任务类型, 提示词, 开始时间)
        except Exception as e:
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)
            logger.error(f"任务 {任务ID} 执行失败: {e}", exc_info=True)
            self._最后健康状态 = False
            return 任务结果(任务ID=任务ID, 状态="failed", 输出数据={}, 制品列表=[], 使用的令牌数=0, 成本=0.0, 耗时毫秒=耗时毫秒, 错误=str(e))

    async def _CLI执行任务(self, 任务ID: str, 任务类型: str, 提示词: str, 上下文: 上下文包, 开始时间: float) -> 任务结果:
        claude_path = self._配置.get("claude_path", "claude")
        超时 = self._配置.get("timeout", 600)
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
            stdout, stderr = await asyncio.wait_for(进程.communicate(), timeout=超时)
        except asyncio.TimeoutError:
            进程.kill()
            await 进程.wait()
            耗时 = int((time.time() - 开始时间) * 1000)
            return 任务结果(任务ID=任务ID, 状态="failed", 输出数据={}, 制品列表=[], 使用的令牌数=0, 成本=0.0, 耗时毫秒=耗时, 错误="Claude Code 任务执行超时")
        finally:
            self._进程 = None
        输出文本 = stdout.decode("utf-8", errors="replace")
        错误文本 = stderr.decode("utf-8", errors="replace")
        if 进程.returncode != 0:
            耗时 = int((time.time() - 开始时间) * 1000)
            return 任务结果(任务ID=任务ID, 状态="failed", 输出数据={"stderr": 错误文本}, 制品列表=[], 使用的令牌数=0, 成本=0.0, 耗时毫秒=耗时, 错误=f"Claude Code 退出码 {进程.returncode}: {错误文本[:500]}")
        制品 = self._提取制品(输出文本)
        耗时 = int((time.time() - 开始时间) * 1000)
        return 任务结果(任务ID=任务ID, 状态="completed", 输出数据={"文本": 输出文本, "任务类型": 任务类型, "模型": f"{claude_path}(CLI)", "工作目录": str(工作目录 or Path.cwd())}, 制品列表=制品, 使用的令牌数=0, 成本=0.0, 耗时毫秒=耗时, 错误=None)

    async def _API执行任务(self, 任务ID: str, 任务类型: str, 提示词: str, 开始时间: float) -> 任务结果:
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
        return 任务结果(任务ID=任务ID, 状态="completed", 输出数据={"文本": 输出文本, "任务类型": 任务类型, "模型": self._模型}, 制品列表=制品, 使用的令牌数=使用的令牌数, 成本=成本, 耗时毫秒=耗时, 错误=None)

    async def 流式执行任务(self, 任务ID: str, 任务类型: str, 输入数据: dict[str, Any], 上下文: 上下文包) -> AsyncIterator[dict[str, Any]]:
        提示词 = self._构建提示词(任务类型, 输入数据, 上下文)
        if self._CLI可用:
            async for 块 in self._CLI流式执行(任务ID, 提示词, 上下文):
                yield 块
        else:
            async for 块 in self._API流式执行(任务ID, 提示词):
                yield 块

    async def _CLI流式执行(self, 任务ID: str, 提示词: str, 上下文: 上下文包) -> AsyncIterator[dict[str, Any]]:
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
                行 = await asyncio.wait_for(进程.stdout.readline(), timeout=超时)
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

    async def _API流式执行(self, 任务ID: str, 提示词: str) -> AsyncIterator[dict[str, Any]]:
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
                        文本 = await asyncio.wait_for(流.text_stream.__anext__(), timeout=超时)
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
