"""资源调度器

管理执行层的资源分配，包括：
- 智能体并发控制
- 任务队列管理
- 资源限制
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class 资源配额:
    """资源配额"""
    最大并发任务: int = 5
    最大并发智能体: int = 3
    任务超时秒: int = 1800
    智能体冷却秒: int = 60


@dataclass
class 智能体状态:
    """智能体状态"""
    ID: str
    忙碌: bool = False
    当前任务ID: str = ""
    最后完成时间: str = ""
    执行次数: int = 0


class 资源调度器:
    """资源调度器
    
    管理执行层的资源分配。
    """

    def __init__(self, 配额: 资源配额 = None):
        self.配额 = 配额 or 资源配额()
        self.智能体状态: dict[str, 智能体状态] = {}
        self.活跃任务数 = 0
        self._锁 = asyncio.Lock()

    def 注册智能体(self, 智能体ID: str):
        """注册智能体"""
        if 智能体ID not in self.智能体状态:
            self.智能体状态[智能体ID] = 智能体状态(ID=智能体ID)

    def 注销智能体(self, 智能体ID: str):
        """注销智能体"""
        self.智能体状态.pop(智能体ID, None)

    async def 申请执行(self, 智能体ID: str, 任务ID: str) -> bool:
        """申请执行资源
        
        Returns:
            是否允许执行
        """
        async with self._锁:
            if self.活跃任务数 >= self.配额.最大并发任务:
                logger.warning(f"达到最大并发任务数: {self.配额.最大并发任务}")
                return False

            状态 = self.智能体状态.get(智能体ID)
            if not 状态:
                self.注册智能体(智能体ID)
                状态 = self.智能体状态[智能体ID]

            if 状态.忙碌:
                logger.warning(f"智能体 {智能体ID} 正在忙碌")
                return False

            状态.忙碌 = True
            状态.当前任务ID = 任务ID
            self.活跃任务数 += 1

            return True

    async def 释放执行(self, 智能体ID: str, 任务ID: str):
        """释放执行资源"""
        async with self._锁:
            状态 = self.智能体状态.get(智能体ID)
            if 状态:
                状态.忙碌 = False
                状态.当前任务ID = ""
                状态.最后完成时间 = datetime.now().isoformat()
                状态.执行次数 += 1

            self.活跃任务数 = max(0, self.活跃任务数 - 1)

    def 获取可用智能体(self) -> list[str]:
        """获取可用智能体列表"""
        return [
            ID for ID, 状态 in self.智能体状态.items()
            if not 状态.忙碌
        ]

    def 获取状态(self) -> dict:
        """获取调度器状态"""
        return {
            "活跃任务数": self.活跃任务数,
            "最大并发任务": self.配额.最大并发任务,
            "智能体数量": len(self.智能体状态),
            "可用智能体": self.获取可用智能体(),
            "智能体状态": {
                ID: {
                    "忙碌": s.忙碌,
                    "当前任务ID": s.当前任务ID,
                    "执行次数": s.执行次数,
                }
                for ID, s in self.智能体状态.items()
            },
        }
