"""OpenCode适配器实现"""
import time
import asyncio
from typing import AsyncIterator, Any
import logging
import json
from pathlib import Path

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

class OpenCode适配器(智能体适配器):
    """
    OpenCode适配器

    通过OpenCode CLI或API执行任务
    支持多种AI模型的通用适配器
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._进程: asyncio.subprocess.Process | None = None
        self._最后健康状态 = False
        self._提示词管理器 = 提示词模板管理器()

    @property
    def 智能体ID(self) -> str:
        return "opencode"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "go", "rust"],
                上下文窗口=128000,
                每千令牌成本=0.001,
                最大并发任务数=3
            ),
            智能体能力(
                名称="code_review",
                语言列表=["python", "javascript", "typescript", "go", "rust"],
                上下文窗口=128000,
                每千令牌成本=0.001,
                最大并发任务数=3
            ),
            智能体能力(
                名称="exploration",
                语言列表=["python", "javascript", "typescript"],
                上下文窗口=128000,
                每千令牌成本=0.001,
                最大并发任务数=3
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.深度

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.便宜

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化OpenCode"""
        self._配置.update(配置)
        opencode_path = 配置.get("path", "opencode")
        logger.info(f"OpenCode适配器初始化 (路径: {opencode_path}, 模型: {self._模型})")

    async def 健康检查(self) -> bool:
        opencode_path = self._配置.get("path", "opencode")
        if Path(opencode_path).exists():
            self._最后健康状态 = True
        return self._最后健康状态

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
            opencode_path = self._配置.get("path", "opencode")

            进程 = await asyncio.create_subprocess_exec(
                opencode_path, "run",
                "--model", self._模型,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self._进程 = 进程
            stdout, stderr = await asyncio.wait_for(
                进程.communicate(提示词.encode()),
                timeout=self._配置.get("timeout", 300)
            )

            输出文本 = stdout.decode("utf-8", errors="replace")
            错误文本 = stderr.decode("utf-8", errors="replace")

            if 进程.returncode != 0:
                raise RuntimeError(f"OpenCode执行失败: {错误文本}")

            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)

            制品 = self._提取制品(输出文本)

            return 任务结果(
                任务ID=任务ID,
                状态="completed",
                输出数据={
                    "文本": 输出文本,
                    "任务类型": 任务类型,
                    "模型": self._模型
                },
                制品列表=制品,
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时毫秒,
                错误=None
            )

        except asyncio.TimeoutError:
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)
            logger.error(f"任务 {任务ID} 执行超时")
            self._最后健康状态 = False
            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时毫秒,
                错误="任务执行超时"
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
        opencode_path = self._配置.get("path", "opencode")
        超时 = self._配置.get("timeout", 300)

        try:
            进程 = await asyncio.create_subprocess_exec(
                opencode_path, "run",
                "--model", self._模型,
                "--stream",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self._进程 = 进程

            进程.stdin.write(提示词.encode())
            await 进程.stdin.drain()
            进程.stdin.close()

            try:
                while True:
                    行 = await asyncio.wait_for(
                        进程.stdout.readline(), timeout=超时
                    )
                    if not 行:
                        break
                    文本 = 行.decode("utf-8", errors="replace").strip()
                    if 文本:
                        yield {"type": "text", "text": 文本}
            except asyncio.TimeoutError:
                logger.error(f"流式任务 {任务ID} 读取超时")
                进程.kill()
                yield {"type": "error", "错误": "流式执行超时"}
                return

            await 进程.wait()
            yield {"type": "done", "任务ID": 任务ID}

        except Exception as e:
            logger.error(f"流式任务 {任务ID} 失败: {e}", exc_info=True)
            yield {"type": "error", "错误": str(e)}

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        if self._进程:
            try:
                self._进程.terminate()
                logger.info(f"任务 {任务ID} 已取消")
                return True
            except Exception as e:
                logger.error(f"取消任务 {任务ID} 失败: {e}")
        return False


