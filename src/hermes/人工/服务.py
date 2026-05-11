"""人工参与服务"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class 审批状态(str, Enum):
    """审批状态"""
    待处理 = "pending"
    已批准 = "approved"
    已拒绝 = "rejected"
    已超时 = "timeout"
    已取消 = "cancelled"

class 审批风险级别(str, Enum):
    """审批风险级别"""
    低 = "low"
    中 = "medium"
    高 = "high"
    关键 = "critical"

@dataclass
class 审批请求:
    """审批请求"""
    ID: str
    流水线ID: str
    阶段ID: str
    请求者: str
    内容描述: str
    制品列表: list[dict[str, Any]] = field(default_factory=list)
    风险级别: 审批风险级别 = 审批风险级别.中
    状态: 审批状态 = 审批状态.待处理
    创建时间: datetime = field(default_factory=datetime.now)
    决策时间: datetime | None = None
    决策者: str | None = None
    反馈: str = ""
    超时秒: int = 300
    自动批准: bool = False  # 低风险自动批准

@dataclass
class 访谈问题:
    """访谈问题"""
    ID: str
    问题内容: str
    问题类型: str = "text"  # text, choice, confirm
    选项列表: list[str] = field(default_factory=list)
    是否必须: bool = True
    默认值: str | None = None

class 人工界面服务:
    """
    人工参与服务

    处理审批请求、访谈模式和通知
    """

    def __init__(self, 默认超时秒: int = 300):
        self.默认超时秒 = 默认超时秒

        self._审批请求: dict[str, 审批请求] = {}
        self._审批事件: dict[str, asyncio.Event] = {}
        self._待处理审批: asyncio.Queue = asyncio.Queue()
        self._通知回调: list[Callable] = []
        self._超时检测任务: asyncio.Task | None = None
        self._运行中 = False

    async def 启动(self):
        """启动人工界面服务"""
        if self._运行中:
            return
        self._运行中 = True
        self._超时检测任务 = asyncio.create_task(self._超时检测循环())
        logger.info("人工界面服务已启动")

    async def 停止(self):
        """停止人工界面服务"""
        self._运行中 = False
        if self._超时检测任务:
            self._超时检测任务.cancel()
            try:
                await self._超时检测任务
            except asyncio.CancelledError:
                pass
        logger.info("人工界面服务已停止")

    def 注册通知回调(self, 回调: Callable):
        """注册通知回调"""
        self._通知回调.append(回调)

    async def 请求审批(
        self,
        流水线ID: str,
        阶段ID: str,
        请求者: str,
        内容描述: str,
        制品列表: list[dict[str, Any]] | None = None,
        风险级别: 审批风险级别 = 审批风险级别.中,
        超时秒: int | None = None
    ) -> bool:
        """
        请求审批

        Returns:
            True 如果已批准，False 如果拒绝或超时
        """
        请求ID = str(uuid4())
        超时 = 超时秒 or self.默认超时秒

        审批 = 审批请求(
            ID=请求ID,
            流水线ID=流水线ID,
            阶段ID=阶段ID,
            请求者=请求者,
            内容描述=内容描述,
            制品列表=制品列表 or [],
            风险级别=风险级别,
            超时秒=超时
        )

        self._审批请求[请求ID] = 审批

        # 低风险自动批准
        if 风险级别 == 审批风险级别.低:
            审批.状态 = 审批状态.已批准
            审批.决策时间 = datetime.now()
            审批.反馈 = "低风险，自动批准"
            logger.info(f"审批 {请求ID} 低风险自动批准")
            return True

        # 通知回调
        for 回调 in self._通知回调:
            try:
                await 回调("审批请求", 审批)
            except Exception as e:
                logger.error(f"通知回调失败: {e}")

        # 等待决策
        事件 = asyncio.Event()
        self._审批事件[请求ID] = 事件

        try:
            await asyncio.wait_for(事件.wait(), timeout=超时)
        except asyncio.TimeoutError:
            审批.状态 = 审批状态.已超时
            审批.决策时间 = datetime.now()
            self._审批事件.pop(请求ID, None)
            logger.warning(f"审批 {请求ID} 超时")
            return False

        self._审批事件.pop(请求ID, None)
        审批 = self._审批请求.get(请求ID)
        if 审批 and 审批.状态 == 审批状态.已批准:
            return True
        return False

    async def 提交决策(
        self,
        请求ID: str,
        决策者: str,
        批准: bool,
        反馈: str = ""
    ) -> bool:
        """提交审批决策"""
        审批 = self._审批请求.get(请求ID)
        if not 审批 or 审批.状态 != 审批状态.待处理:
            return False

        审批.状态 = 审批状态.已批准 if 批准 else 审批状态.已拒绝
        审批.决策者 = 决策者
        审批.决策时间 = datetime.now()
        审批.反馈 = 反馈

        if 请求ID in self._审批事件:
            self._审批事件[请求ID].set()

        logger.info(f"审批 {请求ID} 已{'批准' if 批准 else '拒绝'} (决策者: {决策者})")
        return True

    async def 访谈(
        self,
        流水线ID: str,
        问题列表: list[访谈问题],
        超时秒: int = 600
    ) -> dict[str, str]:
        """
        访谈模式 - 收集用户输入

        Returns:
            问题ID -> 回答的映射
        """
        回答 = {}

        for 问题 in 问题列表:
            # 通知有新问题
            for 回调 in self._通知回调:
                try:
                    await 回调("访谈问题", 问题)
                except Exception as e:
                    logger.error(f"通知回调失败: {e}")

            # 等待回答
            try:
                用户回答 = await asyncio.wait_for(
                    self._等待回答(问题.ID),
                    timeout=超时秒
                )
                回答[问题.ID] = 用户回答
            except asyncio.TimeoutError:
                if 问题.默认值:
                    回答[问题.ID] = 问题.默认值
                elif 问题.是否必须:
                    raise TimeoutError(f"问题 {问题.ID} 回答超时")

        return 回答

    async def _等待回答(self, 问题ID: str) -> str:
        """等待用户回答"""
        # 这里应该有实际的用户交互机制
        # 暂时返回默认值
        await asyncio.sleep(0)
        return ""

    def 获取待处理审批(self) -> list[审批请求]:
        """获取所有待处理的审批请求"""
        return [
            审批 for 审批 in self._审批请求.values()
            if 审批.状态 == 审批状态.待处理
        ]

    def 获取审批历史(self, 流水线ID: str | None = None) -> list[审批请求]:
        """获取审批历史"""
        历史 = [
            审批 for 审批 in self._审批请求.values()
            if 审批.状态 != 审批状态.待处理
        ]
        if 流水线ID:
            历史 = [审批 for 审批 in 历史 if 审批.流水线ID == 流水线ID]
        return sorted(历史, key=lambda x: x.创建时间, reverse=True)

    async def _超时检测循环(self):
        """超时检测循环"""
        while self._运行中:
            try:
                现在 = datetime.now()
                for 审批 in list(self._审批请求.values()):
                    if 审批.状态 == 审批状态.待处理:
                        超时时间 = 审批.创建时间 + timedelta(seconds=审批.超时秒)
                        if 现在 > 超时时间:
                            审批.状态 = 审批状态.已超时
                            审批.决策时间 = 现在
                            logger.warning(f"审批 {审批.ID} 已超时")

                await asyncio.sleep(5)  # 每5秒检查一次
            except Exception as e:
                logger.error(f"超时检测异常: {e}")
                await asyncio.sleep(5)
