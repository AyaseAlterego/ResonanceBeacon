"""智能体健康检查和负载均衡"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import time
import asyncio
import logging

from .基础 import 智能体适配器, 智能体健康状态

logger = logging.getLogger(__name__)

@dataclass
class 健康检查记录:
    """健康检查记录"""
    智能体ID: str
    状态: 智能体健康状态
    检查时间: datetime
    响应时间毫秒: int = 0
    错误信息: str | None = None

@dataclass
class 负载统计:
    """智能体负载统计"""
    智能体ID: str
    当前并发数: int = 0
    最大并发数: int = 5
    累计任务数: int = 0
    成功任务数: int = 0
    失败任务数: int = 0
    平均响应时间毫秒: int = 0
    最后任务时间: datetime | None = None

    @property
    def 负载率(self) -> float:
        """当前负载率 (0.0-1.0)"""
        if self.最大并发数 <= 0:
            return 1.0
        return min(1.0, self.当前并发数 / self.最大并发数)

    @property
    def 成功率(self) -> float:
        """任务成功率"""
        总数 = self.成功任务数 + self.失败任务数
        if 总数 <= 0:
            return 1.0
        return self.成功任务数 / 总数

class 健康检查器:
    """
    智能体健康检查器

    定期检查智能体健康状态，维护负载统计
    """

    def __init__(self, 检查间隔秒: int = 30, 历史记录数: int = 100):
        self.检查间隔秒 = 检查间隔秒
        self.历史记录数 = 历史记录数

        # 健康检查历史
        self._健康记录: dict[str, list[健康检查记录]] = defaultdict(list)
        # 负载统计
        self._负载统计: dict[str, 负载统计] = {}
        # 智能体引用
        self._智能体: dict[str, 智能体适配器] = {}
        # 检查任务
        self._检查任务: asyncio.Task | None = None
        self._运行中 = False

    def 注册智能体(self, 智能体: 智能体适配器):
        """注册智能体用于健康检查"""
        self._智能体[智能体.智能体ID] = 智能体
        if 智能体.智能体ID not in self._负载统计:
            self._负载统计[智能体.智能体ID] = 负载统计(
                智能体ID=智能体.智能体ID,
                最大并发数=5  # 默认值，可从能力列表更新
            )
        logger.debug(f"注册健康检查智能体: {智能体.智能体ID}")

    async def 开始检查(self):
        """开始定期健康检查"""
        if self._运行中:
            return

        self._运行中 = True
        self._检查任务 = asyncio.create_task(self._检查循环())
        logger.info(f"健康检查已启动 (间隔: {self.检查间隔秒}秒)")

    async def 停止检查(self):
        """停止健康检查"""
        self._运行中 = False
        if self._检查任务:
            self._检查任务.cancel()
            try:
                await self._检查任务
            except asyncio.CancelledError:
                pass
        logger.info("健康检查已停止")

    async def _检查循环(self):
        """健康检查循环"""
        while self._运行中:
            try:
                await self._执行健康检查()
            except Exception as e:
                logger.error(f"健康检查异常: {e}", exc_info=True)

            await asyncio.sleep(self.检查间隔秒)

    async def _执行健康检查(self):
        """执行所有智能体的健康检查"""
        for 智能体ID, 智能体 in self._智能体.items():
            try:
                开始时间 = time.time()
                健康 = await 智能体.健康检查()
                响应时间 = int((time.time() - 开始时间) * 1000)

                状态 = 智能体健康状态.健康 if 健康 else 智能体健康状态.不健康

                记录 = 健康检查记录(
                    智能体ID=智能体ID,
                    状态=状态,
                    检查时间=datetime.now(),
                    响应时间毫秒=响应时间
                )

                self._健康记录[智能体ID].append(记录)

                # 限制历史记录数
                if len(self._健康记录[智能体ID]) > self.历史记录数:
                    self._健康记录[智能体ID] = self._健康记录[智能体ID][-self.历史记录数:]

                if not 健康:
                    logger.warning(f"智能体 {智能体ID} 健康检查失败")

            except Exception as e:
                记录 = 健康检查记录(
                    智能体ID=智能体ID,
                    状态=智能体健康状态.不健康,
                    检查时间=datetime.now(),
                    错误信息=str(e)
                )
                self._健康记录[智能体ID].append(记录)
                logger.error(f"智能体 {智能体ID} 健康检查异常: {e}")

    def 获取健康状态(self, 智能体ID: str) -> 智能体健康状态:
        """获取智能体当前健康状态"""
        记录列表 = self._健康记录.get(智能体ID, [])
        if not 记录列表:
            return 智能体健康状态.健康  # 未检查过默认健康

        最新记录 = 记录列表[-1]
        return 最新记录.状态

    def 获取健康率(self, 智能体ID: str, 时间窗口分钟: int = 60) -> float:
        """获取智能体在指定时间窗口内的健康率"""
        记录列表 = self._健康记录.get(智能体ID, [])
        if not 记录列表:
            return 1.0

        截止时间 = datetime.now() - timedelta(minutes=时间窗口分钟)
        窗口记录 = [r for r in 记录列表 if r.检查时间 > 截止时间]

        if not 窗口记录:
            return 1.0

        健康数 = sum(1 for r in 窗口记录 if r.状态 == 智能体健康状态.健康)
        return 健康数 / len(窗口记录)

    def 记录任务开始(self, 智能体ID: str):
        """记录任务开始（增加并发数）"""
        if 智能体ID not in self._负载统计:
            self._负载统计[智能体ID] = 负载统计(智能体ID=智能体ID)
        self._负载统计[智能体ID].当前并发数 += 1
        self._负载统计[智能体ID].累计任务数 += 1
        self._负载统计[智能体ID].最后任务时间 = datetime.now()

    def 记录任务完成(self, 智能体ID: str, 成功: bool, 响应时间毫秒: int = 0):
        """记录任务完成（减少并发数，更新统计）"""
        if 智能体ID not in self._负载统计:
            return

        统计 = self._负载统计[智能体ID]
        统计.当前并发数 = max(0, 统计.当前并发数 - 1)

        if 成功:
            统计.成功任务数 += 1
        else:
            统计.失败任务数 += 1

        # 更新平均响应时间（指数移动平均）
        总任务 = 统计.成功任务数 + 统计.失败任务数
        if 总任务 > 0:
            统计.平均响应时间毫秒 = int(
                (统计.平均响应时间毫秒 * (总任务 - 1) + 响应时间毫秒) / 总任务
            )

    def 获取负载统计(self, 智能体ID: str) -> 负载统计 | None:
        """获取智能体负载统计"""
        return self._负载统计.get(智能体ID)

    def 获取所有负载统计(self) -> dict[str, 负载统计]:
        """获取所有智能体负载统计"""
        return dict(self._负载统计)

    def 获取最低负载智能体(self, 智能体ID列表: list[str]) -> str | None:
        """从候选列表中选择负载最低的智能体"""
        最低负载 = 1.0
        最佳ID = None

        for 智能体ID in 智能体ID列表:
            统计 = self._负载统计.get(智能体ID)
            if 统计 is None:
                return 智能体ID  # 无统计信息视为最低负载

            if 统计.负载率 < 最低负载:
                最低负载 = 统计.负载率
                最佳ID = 智能体ID

        return 最佳ID
