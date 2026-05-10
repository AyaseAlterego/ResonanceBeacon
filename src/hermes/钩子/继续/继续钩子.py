"""继续层钩子工厂"""
from typing import Optional
import logging

from ..基础 import 钩子, 钩子层级, 钩子事件, 钩子上下文, 安全创建钩子

logger = logging.getLogger(__name__)


class 继续钩子工厂:
    """
    继续层钩子工厂

    创建与重试、循环检测和流程继续相关的钩子（失败重试、循环防止等）
    """

    def 创建钩子(self, 上下文: 钩子上下文) -> list[钩子]:
        """创建所有继续层钩子"""
        钩子列表 = [
            安全创建钩子(
                "任务失败重试",
                self._创建任务失败重试,
                上下文
            ),
            安全创建钩子(
                "无限循环检测",
                self._创建无限循环检测,
                上下文
            ),
            安全创建钩子(
                "阶段失败恢复",
                self._创建阶段失败恢复,
                上下文
            ),
        ]

        # 过滤掉None（创建失败的钩子）
        return [h for h in 钩子列表 if h is not None]

    def _创建任务失败重试(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建任务失败重试钩子"""
        def 回调(任务定义, 错误):
            任务ID = 任务定义.get("id", "未知") if isinstance(任务定义, dict) else "未知"
            重试次数 = 任务定义.get("重试次数", 0) if isinstance(任务定义, dict) else 0
            最大重试 = 3

            if 重试次数 < 最大重试:
                logger.info(f"任务 {任务ID} 失败，准备重试 ({重试次数+1}/{最大重试})")
                # 在这里可以实现实际的重试逻辑
                return True  # 返回True表示应该重试
            else:
                logger.warning(f"任务 {任务ID} 已达到最大重试次数 {最大重试}")
                return False  # 返回False表示不应重试

        return 钩子(
            名称="任务失败重试",
            层级=钩子层级.继续,
            事件=钩子事件.任务已失败,
            回调=回调,
            优先级=10,
            描述="在任务失败时自动重试"
        )

    def _创建无限循环检测(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建无限循环检测钩子"""
        def 回调(任务定义):
            # 检测是否存在无限循环
            任务ID = 任务定义.get("id", "未知") if isinstance(任务定义, dict) else "未知"
            依赖项 = 任务定义.get("depends_on", []) if isinstance(任务定义, dict) else []

            # 简单的循环检测：检查任务是否依赖于自身
            if 任务ID in 依赖项:
                logger.error(f"检测到任务 {任务ID} 存在循环依赖")
                return False  # 返回False表示不应继续

            logger.debug(f"循环检测通过: 任务 {任务ID}")
            return True  # 返回True表示可以继续

        return 钩子(
            名称="无限循环检测",
            层级=钩子层级.继续,
            事件=钩子事件.任务已开始,
            回调=回调,
            优先级=15,
            描述="检查循环依赖，防止无限循环"
        )

    def _创建阶段失败恢复(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建阶段失败恢复钩子"""
        def 回调(阶段定义):
            阶段ID = 阶段定义.get("id", "未知") if isinstance(阶段定义, dict) else "未知"

            logger.info(f"阶段失败恢复: {阶段ID}")

            # 在这里可以实现阶段失败恢复逻辑
            # 例如：跳过失败的阶段，继续执行下一个阶段

        return 钩子(
            名称="阶段失败恢复",
            层级=钩子层级.继续,
            事件=钩子事件.阶段已失败,
            回调=回调,
            优先级=8,
            描述="处理阶段失败并决定是否继续"
        )
