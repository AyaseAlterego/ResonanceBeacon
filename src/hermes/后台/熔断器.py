"""熔断器模式实现"""
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

class 熔断器状态(str, Enum):
    """熔断器状态"""
    关闭 = "closed"      # 正常工作
    打开 = "open"        # 拒绝所有请求
    半开 = "half_open"   # 允许少量请求测试

class 熔断器:
    """
    熔断器模式实现

    特性：
    1. 当失败次数超过阈值时，打开熔断器
    2. 熔断器打开期间，拒绝所有请求
    3. 经过恢复时间后，进入半开状态
    4. 半开状态下，允许少量请求测试
    5. 如果测试成功，关闭熔断器；否则重新打开
    """

    def __init__(
        self,
        失败阈值: int = 5,
        恢复超时: int = 60,
        半开请求数: int = 3
    ):
        self.失败阈值 = 失败阈值
        self.恢复超时 = 恢复超时
        self.半开请求数 = 半开请求数

        # 每个智能体的状态
        self._状态: dict[str, 熔断器状态] = defaultdict(lambda: 熔断器状态.关闭)
        self._失败计数: dict[str, int] = defaultdict(int)
        self._最后失败时间: dict[str, float] = defaultdict(float)
        self._半开成功数: dict[str, int] = defaultdict(int)

    def 允许请求(self, 智能体ID: str) -> bool:
        """
        检查是否允许请求

        Returns:
            True 如果允许，False 如果熔断器打开
        """
        当前状态 = self._状态[智能体ID]

        if 当前状态 == 熔断器状态.关闭:
            return True

        elif 当前状态 == 熔断器状态.打开:
            # 检查是否应该进入半开状态
            if time.time() - self._最后失败时间[智能体ID] > self.恢复超时:
                self._状态[智能体ID] = 熔断器状态.半开
                self._半开成功数[智能体ID] = 0
                logger.info(f"智能体 {智能体ID} 熔断器进入半开状态")
                return True
            return False

        elif 当前状态 == 熔断器状态.半开:
            # 半开状态下允许少量请求
            if self._半开成功数[智能体ID] < self.半开请求数:
                return True
            return False

        return False

    def 记录成功(self, 智能体ID: str):
        """记录成功请求"""
        当前状态 = self._状态[智能体ID]

        if 当前状态 == 熔断器状态.关闭:
            # 重置失败计数
            self._失败计数[智能体ID] = 0

        elif 当前状态 == 熔断器状态.半开:
            # 半开状态下记录成功
            self._半开成功数[智能体ID] += 1
            if self._半开成功数[智能体ID] >= self.半开请求数:
                # 关闭熔断器
                self._状态[智能体ID] = 熔断器状态.关闭
                self._失败计数[智能体ID] = 0
                logger.info(f"智能体 {智能体ID} 熔断器关闭（恢复正常）")

    def 记录失败(self, 智能体ID: str):
        """记录失败请求"""
        当前状态 = self._状态[智能体ID]

        if 当前状态 == 熔断器状态.关闭:
            self._失败计数[智能体ID] += 1
            if self._失败计数[智能体ID] >= self.失败阈值:
                # 打开熔断器
                self._状态[智能体ID] = 熔断器状态.打开
                self._最后失败时间[智能体ID] = time.time()
                logger.warning(
                    f"智能体 {智能体ID} 熔断器打开 "
                    f"(连续失败 {self._失败计数[智能体ID]} 次)"
                )

        elif 当前状态 == 熔断器状态.半开:
            # 半开状态下失败，重新打开熔断器
            self._状态[智能体ID] = 熔断器状态.打开
            self._最后失败时间[智能体ID] = time.time()
            logger.warning(f"智能体 {智能体ID} 熔断器重新打开")

    def 获取状态(self, 智能体ID: str) -> 熔断器状态:
        """获取智能体熔断器状态"""
        return self._状态[智能体ID]

    def 获取失败计数(self, 智能体ID: str) -> int:
        """获取智能体失败计数"""
        return self._失败计数[智能体ID]

    def 重置(self, 智能体ID: str):
        """重置熔断器状态"""
        self._状态[智能体ID] = 熔断器状态.关闭
        self._失败计数[智能体ID] = 0
        self._半开成功数[智能体ID] = 0
        logger.info(f"智能体 {智能体ID} 熔断器已重置")
