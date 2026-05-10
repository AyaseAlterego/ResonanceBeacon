"""任务队列 - 本地异步实现"""
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional
from enum import Enum
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class 队列任务状态(str, Enum):
    """队列任务状态"""
    等待中 = "pending"
    运行中 = "running"
    已完成 = "completed"
    失败 = "failed"
    已取消 = "cancelled"

@dataclass
class 队列任务:
    """队列任务"""
    ID: str
    名称: str
    优先级: int = 0
    状态: 队列任务状态 = 队列任务状态.等待中
    执行函数: Callable[..., Coroutine] | None = None
    参数: tuple = ()
    关键字参数: dict[str, Any] = field(default_factory=dict)
    结果: Any = None
    错误: Exception | None = None
    创建时间: datetime = field(default_factory=datetime.now)
    开始时间: datetime | None = None
    完成时间: datetime | None = None
    重试次数: int = 0
    最大重试次数: int = 3

class 本地任务队列:
    """
    本地异步任务队列

    不依赖Redis或Celery，适用于开发和测试
    """

    def __init__(self, 最大队列大小: int = 100, 最大并发: int = 10):
        self.最大队列大小 = 最大队列大小
        self.最大并发 = 最大并发

        self._任务队列: asyncio.Queue = asyncio.Queue(maxsize=最大队列大小)
        self._任务存储: dict[str, 队列任务] = {}
        self._工作器数量 = 0
        self._运行中 = False
        self._信号量 = asyncio.Semaphore(最大并发)
        self._工作器任务列表: list[asyncio.Task] = []

    async def 提交任务(
        self,
        执行函数: Callable[..., Coroutine],
        名称: str = "",
        优先级: int = 0,
        最大重试: int = 3,
        *参数,
        **关键字参数
    ) -> str:
        """
        提交任务到队列

        Returns:
            任务ID
        """
        if self._任务队列.qsize() >= self.最大队列大小:
            raise RuntimeError(f"任务队列已满 (最大: {self.最大队列大小})")

        任务ID = str(uuid4())
        任务 = 队列任务(
            ID=任务ID,
            名称=名称 or f"任务-{任务ID[:8]}",
            优先级=优先级,
            执行函数=执行函数,
            参数=参数,
            关键字参数=关键字参数,
            最大重试次数=最大重试
        )

        self._任务存储[任务ID] = 任务
        await self._任务队列.put(任务ID)

        logger.info(f"任务已提交: {任务.ID} ({任务.名称})")
        return 任务ID

    async def 启动工作器(self, 数量: int = 3):
        """启动工作器"""
        if self._运行中:
            return

        self._运行中 = True
        self._工作器数量 = 数量

        for i in range(数量):
            任务 = asyncio.create_task(self._工作器循环(f"工作器-{i}"))
            self._工作器任务列表.append(任务)

        logger.info(f"已启动 {数量} 个工作器")

    async def 停止工作器(self):
        """停止所有工作器"""
        self._运行中 = False

        # 发送停止信号
        for _ in range(self._工作器数量):
            await self._任务队列.put(None)

        # 等待工作器完成
        if self._工作器任务列表:
            await asyncio.gather(*self._工作器任务列表, return_exceptions=True)

        self._工作器任务列表.clear()
        logger.info("所有工作器已停止")

    async def _工作器循环(self, 工作器名称: str):
        """工作器主循环"""
        logger.debug(f"{工作器名称} 已启动")

        while self._运行中:
            try:
                任务ID = await asyncio.wait_for(
                    self._任务队列.get(),
                    timeout=1.0
                )

                if 任务ID is None:
                    break

                任务 = self._任务存储.get(任务ID)
                if not 任务:
                    continue

                await self._执行任务(工作器名称, 任务)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"{工作器名称} 异常: {e}", exc_info=True)

        logger.debug(f"{工作器名称} 已停止")

    async def _执行任务(self, 工作器名称: str, 任务: 队列任务):
        """执行单个任务"""
        async with self._信号量:
            任务.状态 = 队列任务状态.运行中
            任务.开始时间 = datetime.now()

            logger.info(f"{工作器名称} 开始执行任务: {任务.名称}")

            try:
                结果 = await 任务.执行函数(*任务.参数, **任务.关键字参数)
                任务.结果 = 结果
                任务.状态 = 队列任务状态.已完成
                任务.完成时间 = datetime.now()

                耗时 = (任务.完成时间 - 任务.开始时间).总秒数()
                logger.info(f"{工作器名称} 任务完成: {任务.名称} ({耗时:.2f}秒)")

            except Exception as e:
                任务.错误 = e
                任务.重试次数 += 1

                if 任务.重试次数 < 任务.最大重试次数:
                    任务.状态 = 队列任务状态.等待中
                    logger.warning(
                        f"{工作器名称} 任务失败，准备重试 "
                        f"({任务.重试次数}/{任务.最大重试次数}): {任务.名称}"
                    )
                    await self._任务队列.put(任务.ID)
                else:
                    任务.状态 = 队列任务状态.失败
                    任务.完成时间 = datetime.now()
                    logger.error(f"{工作器名称} 任务最终失败: {任务.名称} - {e}")

    def 获取任务状态(self, 任务ID: str) -> 队列任务状态 | None:
        """获取任务状态"""
        任务 = self._任务存储.get(任务ID)
        return 任务.状态 if 任务 else None

    def 获取任务结果(self, 任务ID: str) -> Any:
        """获取任务结果"""
        任务 = self._任务存储.get(任务ID)
        return 任务.结果 if 任务 else None

    def 获取任务错误(self, 任务ID: str) -> Exception | None:
        """获取任务错误"""
        任务 = self._任务存储.get(任务ID)
        return 任务.错误 if 任务 else None

    def 获取队列大小(self) -> int:
        """获取当前队列大小"""
        return self._任务队列.qsize()

    def 获取所有任务(self) -> dict[str, 队列任务]:
        """获取所有任务"""
        return dict(self._任务存储)
