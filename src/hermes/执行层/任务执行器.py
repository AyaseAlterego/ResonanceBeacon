"""任务执行器

接收编排层的任务指令，调度智能体执行具体任务。
是原流水线引擎的简化版，只负责任务级执行。
"""

import asyncio
from typing import Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime

from ..智能体 import 智能体注册表, 类别路由器, 任务需求
from ..钩子 import 钩子组合器, 钩子上下文, 钩子事件
from ..后台 import 后台任务管理器

logger = logging.getLogger(__name__)


@dataclass
class 任务执行结果:
    """任务执行结果"""
    成功: bool
    任务ID: str = ""
    执行引擎: str = ""
    输出: str = ""
    错误: str = ""
    制品: list[dict] = None
    PR信息: dict = None
    执行时间: str = ""
    元数据: dict = None

    def __post_init__(self):
        if self.制品 is None:
            self.制品 = []
        if self.PR信息 is None:
            self.PR信息 = {}
        if self.元数据 is None:
            self.元数据 = {}
        if not self.执行时间:
            self.执行时间 = datetime.now().isoformat()


class 任务执行器:
    """任务执行器
    
    接收编排层的任务指令，调度智能体执行具体任务。
    """

    def __init__(
        self,
        智能体注册表: 智能体注册表,
        类别路由器: 类别路由器,
        后台管理器: 后台任务管理器,
        项目路径: str = ""
    ):
        self.智能体注册表 = 智能体注册表
        self.类别路由器 = 类别路由器
        self.后台管理器 = 后台管理器
        self.项目路径 = 项目路径
        self.钩子组合器 = 钩子组合器()

    async def 执行任务(self, 任务上下文: dict) -> 任务执行结果:
        """执行单个任务
        
        Args:
            任务上下文: 包含任务信息的字典
                - 卡片ID: Kanban卡片ID
                - 标题: 任务标题
                - 描述: 任务描述
                - 引擎: 执行引擎 (claude_code/opencode/codex)
                - 方法论注入: Superpowers方法论prompt
        
        Returns:
            任务执行结果
        """
        任务ID = 任务上下文.get("卡片ID", "unknown")
        标题 = 任务上下文.get("标题", "")
        描述 = 任务上下文.get("描述", "")
        引擎 = 任务上下文.get("引擎", "opencode")
        方法论注入 = 任务上下文.get("方法论注入", "")

        logger.info(f"开始执行任务: {标题} (引擎: {引擎})")

        try:
            智能体 = self._选择智能体(引擎)
            if not 智能体:
                return 任务执行结果(
                    成功=False,
                    任务ID=任务ID,
                    错误=f"没有可用的智能体: {引擎}",
                )

            提示 = self._构建任务提示(标题, 描述, 方法论注入)

            async def 执行函数():
                return await 智能体.执行任务(
                    任务ID=任务ID,
                    任务类型="code_generation",
                    输入数据={"提示": 提示, "描述": 描述},
                    上下文=None,
                )

            后台任务ID = await self.后台管理器.启动任务(
                任务ID=f"task-{任务ID}",
                智能体ID=智能体.智能体ID,
                执行函数=执行函数,
            )

            成功 = await self.后台管理器.等待任务完成(后台任务ID, 超时=1800)

            if not 成功:
                错误 = self.后台管理器.获取任务错误(后台任务ID)
                return 任务执行结果(
                    成功=False,
                    任务ID=任务ID,
                    执行引擎=引擎,
                    错误=str(错误) if 错误 else "任务超时或失败",
                )

            结果 = self.后台管理器.获取任务结果(后台任务ID)

            logger.info(f"任务 {任务ID} 完成")

            return 任务执行结果(
                成功=True,
                任务ID=任务ID,
                执行引擎=引擎,
                输出=结果.get("输出", ""),
                制品=结果.get("制品", []),
                PR信息=结果.get("PR信息", {}),
                元数据=结果.get("元数据", {}),
            )

        except Exception as e:
            logger.error(f"任务 {任务ID} 执行异常: {e}", exc_info=True)
            return 任务执行结果(
                成功=False,
                任务ID=任务ID,
                执行引擎=引擎,
                错误=str(e),
            )

    def _选择智能体(self, 引擎: str) -> Optional[Any]:
        """根据引擎名称选择智能体"""
        引擎到类别 = {
            "claude_code": "深度",
            "opencode": "快速",
            "codex": "工具",
        }

        类别 = 引擎到类别.get(引擎, "工具")

        需求 = 任务需求(
            能力列表=[],
            预估令牌数=4096,
        )

        return self.类别路由器.选择智能体(类别, 需求)

    def _构建任务提示(self, 标题: str, 描述: str, 方法论注入: str) -> str:
        """构建任务提示"""
        提示 = [
            f"# 任务: {标题}",
            "",
            f"## 描述",
            描述,
            "",
            "---",
            "",
            方法论注入,
        ]

        return "\n".join(提示)
