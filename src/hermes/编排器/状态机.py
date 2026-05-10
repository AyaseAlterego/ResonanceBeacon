"""流水线状态机"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class 流水线状态机:
    """
    流水线状态机

    管理流水线的状态转换，确保状态转换的有效性
    """

    def __init__(self):
        # 定义有效的状态转换
        self.有效转换 = {
            "pending": ["running"],
            "running": ["waiting_approval", "completed", "failed", "cancelled"],
            "waiting_approval": ["running", "cancelled"],
            "failed": ["running"],  # 允许重试
            "completed": [],  # 终态，不允许转换
            "cancelled": [],  # 终态，不允许转换
        }

        self._状态: dict[str, str] = {}

    def 设置状态(self, 实体ID: str, 状态: str):
        """设置实体状态"""
        self._状态[实体ID] = 状态
        logger.debug(f"实体 {实体ID} 状态设置为: {状态}")

    def 获取状态(self, 实体ID: str) -> Optional[str]:
        """获取实体状态"""
        return self._状态.get(实体ID)

    def 验证转换(self, 当前状态: str, 新状态: str) -> bool:
        """
        验证状态转换是否有效

        Returns:
            True 如果转换有效，False 否则
        """
        允许的转换 = self.有效转换.get(当前状态, [])
        return 新状态 in 允许的转换

    def 转换状态(self, 实体ID: str, 新状态: str) -> bool:
        """
        转换状态

        Returns:
            True 如果转换成功，False 如果转换无效
        """
        当前状态 = self._状态.get(实体ID)

        if 当前状态 is None:
            logger.error(f"实体 {实体ID} 不存在")
            return False

        if not self.验证转换(当前状态, 新状态):
            logger.error(
                f"无效的状态转换: {当前状态} -> {新状态} "
                f"(允许的转换: {self.有效转换.get(当前状态, [])})"
            )
            return False

        self._状态[实体ID] = 新状态
        logger.info(f"实体 {实体ID} 状态转换: {当前状态} -> {新状态}")
        return True

    def 获取允许的转换(self, 实体ID: str) -> list[str]:
        """获取实体当前允许的状态转换"""
        当前状态 = self._状态.get(实体ID)
        if 当前状态 is None:
            return []
        return self.有效转换.get(当前状态, [])

    def 是终态(self, 实体ID: str) -> bool:
        """检查实体是否处于终态"""
        当前状态 = self._状态.get(实体ID)
        if 当前状态 is None:
            return True
        return len(self.有效转换.get(当前状态, [])) == 0
