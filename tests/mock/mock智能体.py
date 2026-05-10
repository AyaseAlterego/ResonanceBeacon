"""模拟智能体 - 用于测试"""
import asyncio
from typing import AsyncIterator, Any
import logging

from src.hermes.智能体.基础 import (
    智能体适配器,
    智能体能力,
    智能体类别,
    智能体成本,
    任务结果,
    上下文包
)

logger = logging.getLogger(__name__)

class 模拟智能体(智能体适配器):
    """
    模拟智能体

    用于测试的智能体实现，模拟真实智能体的行为
    """

    def __init__(
        self,
        智能体ID: str = "mock_agent",
        类别: 智能体类别 = 智能体类别.工具,
        延迟秒: float = 0.1,
        失败率: float = 0.0
    ):
        self._智能体ID = 智能体ID
        self._类别 = 类别
        self._延迟秒 = 延迟秒
        self._失败率 = 失败率
        self._初始化 = False

    @property
    def 智能体ID(self) -> str:
        return self._智能体ID

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="general",
                语言列表=["python", "javascript"],
                上下文窗口=100000,
                每千令牌成本=0.001,
                最大并发任务数=5
            )
        ]

    @property
    def 类别(self) -> 智能体类别:
        return self._类别

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.便宜

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化模拟智能体"""
        self._初始化 = True
        logger.debug(f"模拟智能体 {self._智能体ID} 初始化")

    async def 健康检查(self) -> bool:
        """健康检查"""
        return self._初始化

    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        """执行任务"""
        import random

        # 模拟延迟
        await asyncio.sleep(self._延迟秒)

        # 模拟失败
        if random.random() < self._失败率:
            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=int(self._延迟秒 * 1000),
                错误="模拟失败"
            )

        # 成功返回
        return 任务结果(
            任务ID=任务ID,
            状态="completed",
            输出数据={
                "文本": f"模拟输出: {任务类型}",
                "任务类型": 任务类型,
                "模型": "mock"
            },
            制品列表=[
                {
                    "类型": "code",
                    "内容": f"# 模拟代码\nprint('hello from {self._智能体ID}')",
                    "语言": "python"
                }
            ],
            使用的令牌数=100,
            成本=0.001,
            耗时毫秒=int(self._延迟秒 * 1000),
            错误=None
        )

    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行任务"""
        模拟输出 = ["模拟", "输出", "内容"]
        for 块 in 模拟输出:
            await asyncio.sleep(0.05)
            yield {"type": "text", "text": 块}

        yield {"type": "done", "任务ID": 任务ID}

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        return True


class 快速模拟智能体(模拟智能体):
    """快速模拟智能体（无延迟）"""

    def __init__(self, 智能体ID: str = "fast_mock"):
        super().__init__(智能体ID=智能体ID, 延迟秒=0.0)


class 慢速模拟智能体(模拟智能体):
    """慢速模拟智能体（有延迟）"""

    def __init__(self, 智能体ID: str = "slow_mock", 延迟秒: float = 1.0):
        super().__init__(智能体ID=智能体ID, 延迟秒=延迟秒)


class 不可靠模拟智能体(模拟智能体):
    """不可靠的模拟智能体（有失败率）"""

    def __init__(self, 智能体ID: str = "unreliable_mock", 失败率: float = 0.3):
        super().__init__(智能体ID=智能体ID, 失败率=失败率)
