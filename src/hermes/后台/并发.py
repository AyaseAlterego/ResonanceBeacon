"""并发管理器"""
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)

class 并发管理器:
    """
    并发管理器

    管理智能体的并发任务数量，防止过载
    """

    def __init__(self, 每智能体最大并发: int = 5):
        self.每智能体最大并发 = 每智能体最大并发
        self._当前并发: dict[str, int] = defaultdict(int)
        self._锁: asyncio.Lock | None = None

    def _获取锁(self) -> asyncio.Lock:
        if self._锁 is None:
            self._锁 = asyncio.Lock()
        return self._锁

    async def 获取许可(self, 智能体ID: str) -> bool:
        """
        获取并发许可

        Returns:
            True 如果获取成功，False 如果已达到最大并发数
        """
        async with self._获取锁():
            if self._当前并发[智能体ID] < self.每智能体最大并发:
                self._当前并发[智能体ID] += 1
                logger.debug(
                    f"智能体 {智能体ID} 获取并发许可 "
                    f"({self._当前并发[智能体ID]}/{self.每智能体最大并发})"
                )
                return True
            else:
                logger.warning(
                    f"智能体 {智能体ID} 已达到最大并发数 "
                    f"({self._当前并发[智能体ID]}/{self.每智能体最大并发})"
                )
                return False

    async def 释放许可(self, 智能体ID: str):
        """释放并发许可"""
        async with self._获取锁():
            if self._当前并发[智能体ID] > 0:
                self._当前并发[智能体ID] -= 1
                logger.debug(
                    f"智能体 {智能体ID} 释放并发许可 "
                    f"({self._当前并发[智能体ID]}/{self.每智能体最大并发})"
                )

    def 获取当前并发数(self, 智能体ID: str) -> int:
        """获取智能体当前并发数"""
        return self._当前并发[智能体ID]

    def 获取所有并发数(self) -> dict[str, int]:
        """获取所有智能体的并发数"""
        return dict(self._当前并发)
