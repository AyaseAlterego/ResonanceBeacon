"""Codex适配器实现"""
import time
import asyncio
from typing import AsyncIterator, Any
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

class Codex适配器(智能体适配器):
    """
    Codex适配器

    通过Codex CLI或API执行任务
    专注于代码生成和补全
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._客户端 = None
        self._最后健康状态 = False
        self._提示词管理器 = 提示词模板管理器()

    @property
    def 智能体ID(self) -> str:
        return "codex"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "java", "csharp"],
                上下文窗口=16000,
                每千令牌成本=0.0004,
                最大并发任务数=10
            ),
            智能体能力(
                名称="test_generation",
                语言列表=["python", "javascript", "typescript"],
                上下文窗口=16000,
                每千令牌成本=0.0004,
                最大并发任务数=10
            ),
            智能体能力(
                名称="code_explanation",
                语言列表=["python", "javascript", "typescript", "java"],
                上下文窗口=16000,
                每千令牌成本=0.0004,
                最大并发任务数=10
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.专家

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.便宜

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化Codex客户端"""
        self._配置.update(配置)
        try:
            import openai
            self._客户端 = openai.AsyncOpenAI(
                api_key=配置.get("api_key"),
                base_url=配置.get("base_url")
            )
            logger.info(f"Codex适配器初始化成功 (模型: {self._模型})")
        except ImportError:
            logger.warning("未安装openai库，Codex适配器将以模拟模式运行")

    async def 健康检查(self) -> bool:
        if self._客户端 is not None:
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

            if not self._客户端:
                raise RuntimeError("Codex客户端未初始化")

            响应 = await self._客户端.chat.completions.create(
                model=self._模型,
                messages=[{"role": "user", "content": 提示词}],
                max_tokens=self._配置.get("max_tokens", 4096),
                temperature=self._配置.get("temperature", 0.7)
            )

            输出文本 = 响应.choices[0].message.content or ""
            使用的令牌数 = (响应.usage.prompt_tokens or 0) + (响应.usage.completion_tokens or 0)
            成本 = self._计算成本(响应.usage)

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
                使用的令牌数=使用的令牌数,
                成本=成本,
                耗时毫秒=耗时毫秒,
                错误=None
            )

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

    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行任务"""
        提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

        if not self._客户端:
            raise RuntimeError("Codex客户端未初始化")

        超时 = self._配置.get("timeout", 300)

        try:
            响应 = await self._客户端.chat.completions.create(
                model=self._模型,
                messages=[{"role": "user", "content": 提示词}],
                max_tokens=self._配置.get("max_tokens", 4096),
                stream=True
            )

            try:
                while True:
                    块 = await asyncio.wait_for(响应.__anext__(), timeout=超时)
                    if 块.choices[0].delta.content:
                        yield {"type": "text", "text": 块.choices[0].delta.content}
            except StopAsyncIteration:
                pass

            yield {"type": "done", "任务ID": 任务ID}

        except asyncio.TimeoutError:
            logger.error(f"流式任务 {任务ID} 超时")
            yield {"type": "error", "错误": "流式执行超时"}
        except Exception as e:
            logger.error(f"流式任务 {任务ID} 失败: {e}", exc_info=True)
            yield {"type": "error", "错误": str(e)}

    def _计算成本(self, 使用量) -> float:
        输入成本 = (使用量.prompt_tokens or 0) * 0.0004 / 1000
        输出成本 = (使用量.completion_tokens or 0) * 0.0004 / 1000
        return 输入成本 + 输出成本

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        logger.warning(f"Codex适配器不支持取消任务 {任务ID}")
        return False


