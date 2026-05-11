"""钩子组合器，组装五层钩子"""
from typing import Optional
import logging

from .基础 import 钩子, 钩子层级, 钩子事件, 钩子上下文
from .会话 import 会话钩子工厂
from .工具守护 import 工具守护钩子工厂
from .转换 import 转换钩子工厂
from .继续 import 继续钩子工厂
from .技能 import 技能钩子工厂

logger = logging.getLogger(__name__)

class 钩子组合器:
    """
    钩子组合器

    组装五层钩子系统：
    1. 会话钩子（生命周期事件）
    2. 工具守护钩子（工具执行守护）
    3. 转换钩子（消息/上下文变换）
    4. 继续钩子（循环管理，重试）
    5. 技能钩子（技能生命周期）
    """

    def __init__(self):
        self.钩子工厂 = {
            钩子层级.会话: 会话钩子工厂(),
            钩子层级.工具守护: 工具守护钩子工厂(),
            钩子层级.转换: 转换钩子工厂(),
            钩子层级.继续: 继续钩子工厂(),
            钩子层级.技能: 技能钩子工厂(),
        }

    def 组合(self, 上下文: 钩子上下文) -> dict[钩子层级, list[钩子]]:
        """
        组装所有层级的钩子

        Args:
            上下文: 钩子上下文，包含流水线、阶段、任务等信息

        Returns:
            按层级组织的钩子字典
        """
        结果 = {}

        for 层级, 工厂 in self.钩子工厂.items():
            try:
                钩子列表 = 工厂.创建钩子(上下文)
                结果[层级] = 钩子列表
                logger.debug(f"为层级 {层级.value} 创建了 {len(钩子列表)} 个钩子")
            except Exception as e:
                logger.error(f"创建 {层级.value} 层级的钩子失败: {e}")
                结果[层级] = []

        return 结果

    def 触发钩子(
        self,
        钩子字典: dict[钩子层级, list[钩子]],
        事件: 钩子事件,
        *参数
    ):
        """
        触发指定事件的所有钩子

        Args:
            钩子字典: 按层级组织的钩子字典
            事件: 要触发的事件
            *事件参数: 传递给钩子回调的参数
        """
        for 层级, 钩子列表 in 钩子字典.items():
            # 按优先级排序（高优先级先执行）
            已排序钩子 = sorted(钩子列表, key=lambda h: h.优先级, reverse=True)

            for 钩子 in 已排序钩子:
                if 钩子 and 钩子.事件 == 事件:
                    try:
                        结果 = 钩子.回调(*参数)
                        if isinstance(结果, bool) and not 结果:
                            logger.warning(f"钩子 {钩子.名称} 返回 False，继续执行")
                        logger.debug(f"钩子 {钩子.名称} 执行成功")
                    except Exception as e:
                        logger.error(
                            f"钩子 {钩子.名称} 执行失败: {e}",
                            exc_info=True
                        )
                        # 安全创建模式：一个钩子失败不崩溃整个系统

    def 获取钩子数量(self, 钩子字典: dict[钩子层级, list[钩子]]) -> int:
        """获取钩子总数"""
        return sum(len(钩子列表) for 钩子列表 in 钩子字典.values())
