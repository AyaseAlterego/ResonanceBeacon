"""上下文管理器和令牌限制器"""
from dataclasses import dataclass, field
from typing import Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class 令牌预算:
    """令牌预算分配"""
    总预算: int = 200000
    已分配: int = 0

    @property
    def 剩余预算(self) -> int:
        return max(0, self.总预算 - self.已分配)

    @property
    def 使用率(self) -> float:
        if self.总预算 <= 0:
            return 1.0
        return min(1.0, self.已分配 / self.总预算)

    def 分配(self, 数量: int) -> bool:
        """分配令牌，返回是否成功"""
        if self.已分配 + 数量 > self.总预算:
            return False
        self.已分配 += 数量
        return True

    def 释放(self, 数量: int):
        """释放已分配的令牌"""
        self.已分配 = max(0, self.已分配 - 数量)

    def 重置(self):
        """重置预算"""
        self.已分配 = 0

@dataclass
class 上下文片段:
    """上下文片段"""
    来源: str  # 来源阶段/任务ID
    内容: str
    令牌估算: int
    优先级: int = 0  # 0-10，10最高
    是否必须: bool = False

class 上下文管理器:
    """
    上下文管理器

    管理跨阶段的上下文传递、令牌预算分配和上下文压缩
    """

    def __init__(self, 默认令牌预算: int = 200000):
        self.默认令牌预算 = 默认令牌预算
        self._片段存储: dict[str, list[上下文片段]] = {}
        self._阶段上下文: dict[str, dict[str, Any]] = {}

    def 创建阶段上下文(self, 阶段ID: str, 输入数据: dict[str, Any] | None = None):
        """创建新的阶段上下文"""
        self._阶段上下文[阶段ID] = {
            "输入数据": 输入数据 or {},
            "制品": [],
            "中间结果": {},
            "令牌使用": 0
        }

    def 添加片段(
        self,
        阶段ID: str,
        来源: str,
        内容: str,
        优先级: int = 0,
        是否必须: bool = False
    ):
        """添加上下文片段"""
        if 阶段ID not in self._片段存储:
            self._片段存储[阶段ID] = []

        片段 = 上下文片段(
            来源=来源,
            内容=内容,
            令牌估算=self._估算令牌数(内容),
            优先级=优先级,
            是否必须=是否必须
        )

        self._片段存储[阶段ID].append(片段)

    def 获取优化上下文(
        self,
        阶段ID: str,
        令牌预算: int | None = None
    ) -> dict[str, Any]:
        """
        获取优化后的上下文

        根据令牌预算，智能选择最重要的上下文片段
        """
        预算 = 令牌预算 or self.默认令牌预算
        片段列表 = self._片段存储.get(阶段ID, [])
        阶段上下文 = self._阶段上下文.get(阶段ID, {})

        结果 = {
            "输入数据": 阶段上下文.get("输入数据", {}),
            "制品": 阶段上下文.get("制品", []),
            "上下文片段": [],
            "总令牌估算": 0
        }

        # 首先添加必须的片段
        剩余预算 = 预算
        for 片段 in 片段列表:
            if 片段.是否必须:
                if 剩余预算 >= 片段.令牌估算:
                    结果["上下文片段"].append({
                        "来源": 片段.来源,
                        "内容": 片段.内容,
                        "令牌估算": 片段.令牌估算
                    })
                    剩余预算 -= 片段.令牌估算
                    结果["总令牌估算"] += 片段.令牌估算

        # 按优先级排序填充剩余预算
        已添加来源 = {片段.来源 for 片段 in 结果["上下文片段"]}
        按优先级排序 = sorted(片段列表, key=lambda x: x.优先级, reverse=True)

        for 片段 in 按优先级排序:
            if 片段.来源 in 已添加来源:
                continue
            if 剩余预算 >= 片段.令牌估算:
                结果["上下文片段"].append({
                    "来源": 片段.来源,
                    "内容": 片段.内容,
                    "令牌估算": 片段.令牌估算
                })
                剩余预算 -= 片段.令牌估算
                结果["总令牌估算"] += 片段.令牌估算

        return 结果

    def 记录制品(self, 阶段ID: str, 制品: dict[str, Any]):
        """记录阶段产出的制品"""
        if 阶段ID not in self._阶段上下文:
            self._阶段上下文[阶段ID] = {}

        if "制品" not in self._阶段上下文[阶段ID]:
            self._阶段上下文[阶段ID]["制品"] = []

        self._阶段上下文[阶段ID]["制品"].append(制品)

    def 记录中间结果(self, 阶段ID: str, 键: str, 值: Any):
        """记录中间结果"""
        if 阶段ID not in self._阶段上下文:
            self._阶段上下文[阶段ID] = {}
        self._阶段上下文[阶段ID].setdefault("中间结果", {})[键] = 值

    def 获取前序制品(self, 当前阶段ID: str) -> list[dict[str, Any]]:
        """获取当前阶段之前所有阶段的制品"""
        所有制品 = []
        for 阶段ID, 上下文 in self._阶段上下文.items():
            if 阶段ID != 当前阶段ID:
                所有制品.append(上下文.get("制品", []))

        # 展平列表
        结果 = []
        for 制品列表 in 所有制品:
            结果.append(制品列表)
        return 结果

    def 压缩上下文(self, 内容: str, 目标令牌数: int) -> str:
        """
        压缩上下文到目标令牌数

        简单策略：截断并添加省略标记
        """
        当前令牌 = self._估算令牌数(内容)

        if 当前令牌 <= 目标令牌数:
            return 内容

        # 简单截断策略（实际应使用更智能的压缩）
        比例 = 目标令牌数 / 当前令牌
        截断位置 = int(len(内容) * 比例)
        return 内容[:截断位置] + "\n\n[... 内容已压缩 ...]"

    def 清理阶段(self, 阶段ID: str):
        """清理阶段上下文"""
        self._片段存储.pop(阶段ID, None)
        self._阶段上下文.pop(阶段ID, None)

    def 清空(self):
        """清空所有上下文"""
        self._片段存储.clear()
        self._阶段上下文.clear()

    def _估算令牌数(self, 文本: str) -> int:
        """估算文本的令牌数（简单估算：约4个字符为1个令牌）"""
        return max(1, len(文本) // 4)
