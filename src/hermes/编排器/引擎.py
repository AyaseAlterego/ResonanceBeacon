"""流水线引擎"""
import asyncio
from typing import Optional
from dataclasses import dataclass
import logging

from .状态机 import 流水线状态机
from ..智能体 import 智能体注册表, 类别路由器, 任务需求
from ..钩子 import 钩子组合器, 钩子上下文, 钩子事件
from ..后台 import 后台任务管理器

logger = logging.getLogger(__name__)

@dataclass
class 流水线结果:
    """流水线执行结果"""
    状态: str  # "completed", "failed", "cancelled"
    流水线ID: str = ""
    阶段数: int = 0
    完成阶段数: int = 0
    总任务数: int = 0
    完成任务数: int = 0
    错误: Optional[str] = None
    制品: list[dict] = None

    def __post_init__(self):
        if self.制品 is None:
            self.制品 = []

class 流水线引擎:
    """
    流水线引擎

    编排流水线的执行，管理阶段和任务的调度
    """

    def __init__(
        self,
        智能体注册表: 智能体注册表,
        类别路由器: 类别路由器,
        后台管理器: 后台任务管理器
    ):
        self.智能体注册表 = 智能体注册表
        self.类别路由器 = 类别路由器
        self.后台管理器 = 后台管理器
        self.状态机 = 流水线状态机()
        self.钩子组合器 = 钩子组合器()

    async def 运行流水线(
        self,
        流水线定义: dict,
        用户输入: str
    ) -> 流水线结果:
        """
        运行流水线

        Args:
            流水线定义: 流水线定义字典（包含阶段、任务等）
            用户输入: 用户的原始输入

        Returns:
            流水线执行结果
        """
        流水线ID = 流水线定义.get("id", "unknown")
        流水线名称 = 流水线定义.get("name", "未命名流水线")

        logger.info(f"开始运行流水线: {流水线名称} (ID: {流水线ID})")

        # 初始化钩子上下文
        上下文 = 钩子上下文(
            流水线=流水线定义,
            元数据={"用户输入": 用户输入}
        )

        # 组装钩子
        钩子字典 = self.钩子组合器.组合(上下文)

        # 触发流水线启动钩子
        self.钩子组合器.触发钩子(钩子字典, 钩子事件.流水线已启动, 流水线定义)

        try:
            # 设置初始状态
            self.状态机.设置状态(流水线ID, "pending")
            self.状态机.转换状态(流水线ID, "running")

            # 获取阶段列表
            阶段列表 = 流水线定义.get("stages", [])
            if not 阶段列表:
                logger.warning(f"流水线 {流水线ID} 没有定义任何阶段")
                return 流水线结果(
                    状态="completed",
                    流水线ID=流水线ID,
                    阶段数=0,
                    完成阶段数=0
                )

            # 按顺序执行阶段
            完成阶段数 = 0
            for 阶段定义 in 阶段列表:
                阶段结果 = await self._执行阶段(
                    流水线ID, 阶段定义, 钩子字典, 上下文
                )

                if 阶段结果["状态"] != "completed":
                    # 阶段失败或取消
                    self.状态机.转换状态(流水线ID, "failed")
                    self.钩子组合器.触发钩子(
                        钩子字典,
                        钩子事件.流水线已失败,
                        流水线定义,
                        阶段结果.get("错误")
                    )

                    return 流水线结果(
                        状态="failed",
                        流水线ID=流水线ID,
                        阶段数=len(阶段列表),
                        完成阶段数=完成阶段数,
                        错误=阶段结果.get("错误")
                    )

                完成阶段数 += 1

            # 所有阶段完成
            self.状态机.转换状态(流水线ID, "completed")
            self.钩子组合器.触发钩子(
                钩子字典,
                钩子事件.流水线已完成,
                流水线定义
            )

            logger.info(f"流水线 {流水线ID} 完成")

            return 流水线结果(
                状态="completed",
                流水线ID=流水线ID,
                阶段数=len(阶段列表),
                完成阶段数=完成阶段数
            )

        except Exception as e:
            logger.error(f"流水线 {流水线ID} 执行异常: {e}", exc_info=True)
            self.状态机.转换状态(流水线ID, "failed")
            self.钩子组合器.触发钩子(
                钩子字典,
                钩子事件.流水线已失败,
                流水线定义,
                e
            )

            return 流水线结果(
                状态="failed",
                流水线ID=流水线ID,
                错误=str(e)
            )

    async def _执行阶段(
        self,
        流水线ID: str,
        阶段定义: dict,
        钩子字典: dict,
        上下文: 钩子上下文
    ) -> dict:
        """执行单个阶段"""
        阶段ID = 阶段定义.get("id", "unknown")
        阶段名称 = 阶段定义.get("name", "未命名阶段")
        阶段类型 = 阶段定义.get("type", "sequential")

        logger.info(f"开始执行阶段: {阶段名称} (类型: {阶段类型})")

        # 触发阶段开始钩子
        self.钩子组合器.触发钩子(钩子字典, 钩子事件.阶段已开始, 阶段定义)

        try:
            # 获取任务列表
            任务列表 = 阶段定义.get("tasks", [])
            if not 任务列表:
                logger.warning(f"阶段 {阶段ID} 没有定义任何任务")
                return {"状态": "completed", "错误": None}

            if 阶段类型 == "parallel":
                # 并发执行任务
                任务结果列表 = await asyncio.gather(
                    *[self._执行任务(流水线ID, 阶段ID, 任务定义, 钩子字典, 上下文)
                      for 任务定义 in 任务列表],
                    return_exceptions=True
                )

                # 检查任务结果
                for 结果 in 任务结果列表:
                    if isinstance(结果, Exception):
                        return {"状态": "failed", "错误": str(结果)}
                    if 结果["状态"] != "completed":
                        return 结果

            else:
                # 顺序执行任务
                for 任务定义 in 任务列表:
                    任务结果 = await self._执行任务(
                        流水线ID, 阶段ID, 任务定义, 钩子字典, 上下文
                    )
                    if 任务结果["状态"] != "completed":
                        return 任务结果

            # 触发阶段完成钩子
            self.钩子组合器.触发钩子(钩子字典, 钩子事件.阶段已完成, 阶段定义)

            logger.info(f"阶段 {阶段ID} 完成")
            return {"状态": "completed", "错误": None}

        except Exception as e:
            logger.error(f"阶段 {阶段ID} 执行异常: {e}", exc_info=True)
            return {"状态": "failed", "错误": str(e)}

    async def _执行任务(
        self,
        流水线ID: str,
        阶段ID: str,
        任务定义: dict,
        钩子字典: dict,
        上下文: 钩子上下文
    ) -> dict:
        """执行单个任务"""
        任务ID = 任务定义.get("id", "unknown")
        任务名称 = 任务定义.get("name", "未命名任务")
        任务类别 = 任务定义.get("category", "utility")

        logger.info(f"开始执行任务: {任务名称} (类别: {任务类别})")

        # 触发任务开始钩子
        self.钩子组合器.触发钩子(钩子字典, 钩子事件.任务已开始, 任务定义)

        try:
            # 根据类别选择智能体
            需求 = 任务需求(
                能力列表=任务定义.get("capabilities", []),
                预估令牌数=任务定义.get("estimated_tokens", 1000)
            )

            # 将类别字符串转换为智能体类别枚举
            from ..智能体.基础 import 智能体类别
            try:
                类别 = 智能体类别(任务类别)
            except ValueError:
                类别 = 智能体类别.工具  # 默认类别

            智能体 = self.类别路由器.选择智能体(类别, 需求)
            if not 智能体:
                return {"状态": "failed", "错误": f"没有可用的智能体处理类别: {任务类别}"}

            logger.info(f"为任务 {任务ID} 选择智能体: {智能体.智能体ID}")

            # 执行任务（后台执行）
            async def 执行函数():
                return await 智能体.执行任务(
                    任务ID,
                    任务定义.get("type", "general"),
                    任务定义.get("input", {}),
                    上下文
                )

            后台任务ID = await self.后台管理器.启动任务(
                任务ID=f"{流水线ID}-{阶段ID}-{任务ID}",
                智能体ID=智能体.智能体ID,
                执行函数=执行函数
            )

            # 等待任务完成
            成功 = await self.后台管理器.等待任务完成(后台任务ID, 超时=600)

            if not 成功:
                错误 = self.后台管理器.获取任务错误(后台任务ID)
                return {"状态": "failed", "错误": str(错误) if 错误 else "任务超时或失败"}

            结果 = self.后台管理器.获取任务结果(后台任务ID)

            # 触发任务完成钩子
            self.钩子组合器.触发钩子(钩子字典, 钩子事件.任务已完成, 任务定义, 结果)

            logger.info(f"任务 {任务ID} 完成")
            return {"状态": "completed", "错误": None, "结果": 结果}

        except Exception as e:
            logger.error(f"任务 {任务ID} 执行异常: {e}", exc_info=True)
            self.钩子组合器.触发钩子(
                钩子字典,
                钩子事件.任务已失败,
                任务定义,
                e
            )
            return {"状态": "failed", "错误": str(e)}
