"""后台任务管理器"""
import asyncio
import time
from typing import Optional
from uuid import uuid4
import logging

from .并发 import 并发管理器
from .熔断器 import 熔断器

logger = logging.getLogger(__name__)

class 后台任务管理器:
    """
    后台任务管理器

    负责任务的异步执行、并发控制、失败处理和熔断器集成
    """

    def __init__(
        self,
        每智能体最大并发: int = 5,
        熔断器阈值: int = 5,
        熔断器恢复时间: int = 60,
        任务超时: int = 600
    ):
        self.并发管理器 = 并发管理器(每智能体最大并发)
        self.熔断器 = 熔断器(熔断器阈值, 熔断器恢复时间)
        self.任务超时 = 任务超时

        # 任务状态跟踪
        self._任务状态: dict[str, str] = {}
        self._任务结果: dict[str, any] = {}
        self._任务错误: dict[str, Exception] = {}
        self._运行中任务: dict[str, asyncio.Task] = {}
        self._任务事件: dict[str, asyncio.Event] = {}
        self._任务完成时间: dict[str, float] = {}
        self._最大保留任务数: int = 1000
        self._任务过期时间: int = 3600

    async def 启动任务(
        self,
        任务ID: str,
        智能体ID: str,
        执行函数,
        *参数,
        **关键字参数
    ) -> str:
        """
        启动后台任务

        Args:
            任务ID: 任务唯一标识（如果不提供则自动生成）
            智能体ID: 智能体标识
            执行函数: 要执行的异步函数
            *参数: 位置参数
            **关键字参数: 关键字参数

        Returns:
            任务ID
        """
        if not 任务ID:
            任务ID = str(uuid4())

        # 检查熔断器
        if not self.熔断器.允许请求(智能体ID):
            raise RuntimeError(f"智能体 {智能体ID} 熔断器已打开，拒绝请求")

        # 检查并发限制
        if not await self.并发管理器.获取许可(智能体ID):
            raise RuntimeError(f"智能体 {智能体ID} 已达到最大并发数")

        self._任务状态[任务ID] = "pending"
        self._任务事件[任务ID] = asyncio.Event()

        # 启动后台任务
        任务 = asyncio.create_task(
            self._执行任务(任务ID, 智能体ID, 执行函数, *参数, **关键字参数)
        )
        self._运行中任务[任务ID] = 任务

        logger.info(f"启动后台任务: {任务ID} (智能体: {智能体ID})")

        return 任务ID

    async def _执行任务(
        self,
        任务ID: str,
        智能体ID: str,
        执行函数,
        *参数,
        **关键字参数
    ):
        """执行后台任务"""
        try:
            self._任务状态[任务ID] = "running"

            # 带超时执行
            结果 = await asyncio.wait_for(
                执行函数(*参数, **关键字参数),
                timeout=self.任务超时
            )

            self._任务状态[任务ID] = "completed"
            self._任务结果[任务ID] = 结果
            self.熔断器.记录成功(智能体ID)

            logger.info(f"任务 {任务ID} 完成")

        except asyncio.TimeoutError:
            self._任务状态[任务ID] = "failed"
            self._任务错误[任务ID] = TimeoutError(f"任务超时 ({self.任务超时}秒)")
            self.熔断器.记录失败(智能体ID)
            logger.error(f"任务 {任务ID} 超时")

        except Exception as e:
            self._任务状态[任务ID] = "failed"
            self._任务错误[任务ID] = e
            self.熔断器.记录失败(智能体ID)
            logger.error(f"任务 {任务ID} 失败: {e}", exc_info=True)

        finally:
            self._运行中任务.pop(任务ID, None)
            self._任务完成时间[任务ID] = time.time()
            事件 = self._任务事件.get(任务ID)
            if 事件:
                事件.set()
            # 释放并发许可
            await self.并发管理器.释放许可(智能体ID)
            self._清理过期任务()

    def 获取任务状态(self, 任务ID: str) -> Optional[str]:
        """获取任务状态"""
        self._清理过期任务()
        return self._任务状态.get(任务ID)

    def 获取任务结果(self, 任务ID: str) -> Optional[any]:
        """获取任务结果"""
        return self._任务结果.get(任务ID)

    def 获取任务错误(self, 任务ID: str) -> Optional[Exception]:
        """获取任务错误"""
        return self._任务错误.get(任务ID)

    async def 等待任务完成(self, 任务ID: str, 超时: int = None) -> bool:
        """
        等待任务完成

        Returns:
            True 如果任务成功完成，False 如果超时或失败
        """
        超时 = 超时 or self.任务超时
        try:
            事件 = self._任务事件.get(任务ID)
            if 事件:
                await asyncio.wait_for(事件.wait(), timeout=超时)
            状态 = self.获取任务状态(任务ID)
            return 状态 == "completed"
        except (asyncio.TimeoutError, Exception):
            return False

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        状态 = self.获取任务状态(任务ID)
        if 状态 in ("pending", "running"):
            self._任务状态[任务ID] = "cancelled"
            任务 = self._运行中任务.pop(任务ID, None)
            if 任务:
                任务.cancel()
                try:
                    await 任务
                except asyncio.CancelledError:
                    pass
            if self._任务事件.get(任务ID):
                self._任务事件[任务ID].set()
            logger.info(f"任务 {任务ID} 已取消")
            return True
        return False

    def _清理过期任务(self):
        """清理过期任务，防止内存泄漏"""
        if len(self._任务状态) <= self._最大保留任务数:
            return
        now = time.time()
        to_delete = []
        for 任务ID, 状态 in list(self._任务状态.items()):
            if 状态 in ("completed", "failed", "cancelled"):
                完成时间 = self._任务完成时间.get(任务ID, 0)
                if 完成时间 and now - 完成时间 > self._任务过期时间:
                    to_delete.append(任务ID)
        for 任务ID in to_delete:
            del self._任务状态[任务ID]
            self._任务结果.pop(任务ID, None)
            self._任务错误.pop(任务ID, None)
            self._任务事件.pop(任务ID, None)
            self._任务完成时间.pop(任务ID, None)

    def 获取所有任务状态(self) -> dict[str, str]:
        """获取所有任务状态"""
        # 清理过期任务
        self._清理过期任务()
        return dict(self._任务状态)
