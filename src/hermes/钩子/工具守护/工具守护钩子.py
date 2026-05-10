"""工具守护层钩子工厂"""
from typing import Optional
import logging

from ..基础 import 钩子, 钩子层级, 钩子事件, 钩子上下文, 安全创建钩子

logger = logging.getLogger(__name__)


class 工具守护钩子工厂:
    """
    工具守护层钩子工厂

    创建与任务执行前后守护相关的钩子（验证、权限、日志记录等）
    """

    def 创建钩子(self, 上下文: 钩子上下文) -> list[钩子]:
        """创建所有工具守护层钩子"""
        钩子列表 = [
            安全创建钩子(
                "任务输入验证",
                self._创建任务输入验证,
                上下文
            ),
            安全创建钩子(
                "任务权限检查",
                self._创建任务权限检查,
                上下文
            ),
            安全创建钩子(
                "任务结果记录",
                self._创建任务结果记录,
                上下文
            ),
            安全创建钩子(
                "任务错误处理",
                self._创建任务错误处理,
                上下文
            ),
        ]

        # 过滤掉None（创建失败的钩子）
        return [h for h in 钩子列表 if h is not None]

    def _创建任务输入验证(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建任务输入验证钩子"""
        def 回调(任务定义):
            # 验证任务定义是否包含必要字段
            必要字段 = ["id", "name", "type"]
            for 字段 in 必要字段:
                if 字段 not in 任务定义:
                    logger.warning(f"任务定义缺少必要字段: {字段}")
                    return False

            logger.debug(f"任务输入验证通过: {任务定义.get('id', '未知')}")
            return True

        return 钩子(
            名称="任务输入验证",
            层级=钩子层级.工具守护,
            事件=钩子事件.任务已开始,
            回调=回调,
            优先级=10,
            描述="验证任务输入数据的完整性和有效性"
        )

    def _创建任务权限检查(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建任务权限检查钩子"""
        def 回调(任务定义):
            # 检查任务是否有执行权限
            类别 = 任务定义.get("category", "utility")

            # 暂时允许所有类别
            logger.debug(f"任务权限检查通过: 类别={类别}")
            return True

        return 钩子(
            名称="任务权限检查",
            层级=钩子层级.工具守护,
            事件=钩子事件.任务已开始,
            回调=回调,
            优先级=9,
            描述="检查任务是否有执行权限"
        )

    def _创建任务结果记录(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建任务结果记录钩子"""
        def 回调(任务定义, 结果):
            任务ID = 任务定义.get("id", "未知") if isinstance(任务定义, dict) else "未知"
            状态 = 结果.get("状态", "未知") if isinstance(结果, dict) else "未知"

            logger.info(f"任务完成记录: {任务ID}, 状态={状态}")

            # 记录任务执行结果
            if isinstance(结果, dict) and 结果.get("状态") == "completed":
                logger.debug(f"任务 {任务ID} 成功完成")
            else:
                logger.warning(f"任务 {任务ID} 未成功完成")

        return 钩子(
            名称="任务结果记录",
            层级=钩子层级.工具守护,
            事件=钩子事件.任务已完成,
            回调=回调,
            优先级=5,
            描述="记录任务执行结果"
        )

    def _创建任务错误处理(self, 上下文: 钩子上下文) -> Optional[钩子]:
        """创建任务错误处理钩子"""
        def 回调(任务定义, 错误):
            任务ID = 任务定义.get("id", "未知") if isinstance(任务定义, dict) else "未知"

            logger.error(f"任务错误处理: 任务={任务ID}, 错误={错误}")

            # 尝试恢复或重试
            # 目前只记录日志，不做实际恢复

        return 钩子(
            名称="任务错误处理",
            层级=钩子层级.工具守护,
            事件=钩子事件.任务已失败,
            回调=回调,
            优先级=8,
            描述="处理任务执行错误"
        )
