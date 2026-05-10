"""技能层钩子工厂"""
from typing import Optional
import logging

from ..基础 import 钩子, 钩子层级, 钩子事件, 钩子上下文, 安全创建钩子

logger = logging.getLogger(__name__)


class 技能钩子工厂:
    """
    技能层钩子工厂

    创建与技能触发和评估相关的钩子（技能需求检测、技能执行评估等）
    """

    def 创建钩子(self, 上下文: 钩子上下文) -> list[钩子]:
        """创建所有技能层钩子"""
        钩子列表 = [
            安全创建钩子(
                "技能需求检测",
                self._创建技能需求检测,
                上下文
            ),
            安全创建钩子(
                "技能执行评估",
                self._创建技能执行评估,
                上下文
            ),
        ]

        # 过滤掉None（创建失败的钩子）
        return [h for h in 钩子列表 if h is not None]

    def _创建技能需求检测(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建技能需求检测钩子"""
        def 回调(任务定义):
            # 检测任务是否需要特定技能
            任务类型 = 任务定义.get("type", "general") if isinstance(任务定义, dict) else "general"
            类别 = 任务定义.get("category", "utility") if isinstance(任务定义, dict) else "utility"

            logger.debug(f"技能需求检测: 任务类型={任务类型}, 类别={类别}")

            # 在这里可以实现技能需求检测逻辑
            # 例如：根据任务类型和类别判断是否需要特定技能

            # 返回技能名称列表（如果需要技能）
            需要的技能 = []

            if 任务类型 == "code_generation":
                需要的技能.append("代码生成")
            elif 任务类型 == "code_review":
                需要的技能.append("代码审查")
            elif 任务类型 == "testing":
                需要的技能.append("测试生成")

            if 需要的技能:
                logger.info(f"检测到技能需求: {需要的技能}")

            return 需要的技能

        return 钩子(
            名称="技能需求检测",
            层级=钩子层级.技能,
            事件=钩子事件.任务已开始,
            回调=回调,
            优先级=5,
            描述="检测任务是否需要特定技能"
        )

    def _创建技能执行评估(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建技能执行评估钩子"""
        def 回调(任务定义, 结果):
            # 评估技能执行结果
            任务ID = 任务定义.get("id", "未知") if isinstance(任务定义, dict) else "未知"

            logger.debug(f"技能执行评估: 任务={任务ID}")

            # 在这里可以实现技能执行评估逻辑
            # 例如：评估技能执行的质量、效率等

            if isinstance(结果, dict) and 结果.get("状态") == "completed":
                logger.info(f"技能执行成功: 任务 {任务ID}")
                return True
            else:
                logger.warning(f"技能执行可能未成功: 任务 {任务ID}")
                return False

        return 钩子(
            名称="技能执行评估",
            层级=钩子层级.技能,
            事件=钩子事件.任务已完成,
            回调=回调,
            优先级=5,
            描述="评估技能执行结果"
        )
