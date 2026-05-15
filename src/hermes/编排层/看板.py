"""Kanban 状态机

管理看板卡片的状态转换：
backlog → in_progress → review → done

每个转换都有严格的守卫条件和副作用。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class Kanban状态(Enum):
    """Kanban 状态枚举"""
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


状态转换规则 = {
    Kanban状态.BACKLOG: [Kanban状态.IN_PROGRESS, Kanban状态.CANCELLED],
    Kanban状态.IN_PROGRESS: [Kanban状态.REVIEW, Kanban状态.BACKLOG],
    Kanban状态.REVIEW: [Kanban状态.DONE, Kanban状态.IN_PROGRESS],
    Kanban状态.DONE: [],
    Kanban状态.CANCELLED: [],
}


@dataclass
class Kanban卡片:
    """Kanban 卡片数据模型"""
    ID: str
    项目ID: str
    标题: str
    描述: str = ""
    状态: str = "backlog"
    优先级: str = "medium"
    负责人: str = "dev"
    来源: str = "manual"
    复杂度: str = "medium"
    预估工时: str = "未知"
    等待审批: bool = False
    关联任务ID: str = ""
    关联制品ID列表: list[str] = field(default_factory=list)
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())
    更新时间: str = field(default_factory=lambda: datetime.now().isoformat())
    完成时间: str = ""
    元数据: dict = field(default_factory=dict)


@dataclass
class 状态转换记录:
    """状态转换历史记录"""
    ID: str
    卡片ID: str
    从状态: str
    到状态: str
    触发者: str
    原因: str = ""
    时间: str = field(default_factory=lambda: datetime.now().isoformat())


class Kanban状态机:
    """Kanban 状态机
    
    管理卡片状态转换，确保转换合法并记录历史。
    """

    def __init__(self):
        self.卡片列表: dict[str, Kanban卡片] = {}
        self.转换历史: list[状态转换记录] = []

    def 创建卡片(self, 数据: dict) -> Kanban卡片:
        """创建新卡片"""
        import uuid
        卡片ID = f"card-{uuid.uuid4().hex[:8]}"

        卡片 = Kanban卡片(
            ID=卡片ID,
            项目ID=数据.get("项目ID", ""),
            标题=数据.get("标题", "未命名"),
            描述=数据.get("描述", ""),
            状态=数据.get("状态", "backlog"),
            优先级=数据.get("优先级", "medium"),
            负责人=数据.get("负责人", "dev"),
            来源=数据.get("来源", "manual"),
            复杂度=数据.get("复杂度", "medium"),
            预估工时=数据.get("预估工时", "未知"),
            元数据=数据.get("元数据", {}),
        )

        self.卡片列表[卡片ID] = 卡片
        return 卡片

    def 获取卡片(self, 卡片ID: str) -> Optional[Kanban卡片]:
        """获取卡片"""
        return self.卡片列表.get(卡片ID)

    def 获取项目卡片(self, 项目ID: str) -> list[Kanban卡片]:
        """获取项目的所有卡片"""
        return [c for c in self.卡片列表.values() if c.项目ID == 项目ID]

    def 获取看板状态(self, 项目ID: str) -> dict[str, list[Kanban卡片]]:
        """获取项目的完整看板状态"""
        卡片列表 = self.获取项目卡片(项目ID)

        return {
            "backlog": [c for c in 卡片列表 if c.状态 == "backlog"],
            "in_progress": [c for c in 卡片列表 if c.状态 == "in_progress"],
            "review": [c for c in 卡片列表 if c.状态 == "review"],
            "done": [c for c in 卡片列表 if c.状态 == "done"],
            "cancelled": [c for c in 卡片列表 if c.状态 == "cancelled"],
        }

    def 转换状态(self, 卡片ID: str, 目标状态: str, 触发者: str = "system", 原因: str = "") -> dict:
        """转换卡片状态
        
        返回: {"成功": bool, "卡片": Kanban卡片, "错误": str}
        """
        卡片 = self.获取卡片(卡片ID)
        if not 卡片:
            return {"成功": False, "错误": "卡片不存在"}

        当前状态 = Kanban状态(卡片.状态)
        try:
            目标状态枚举 = Kanban状态(目标状态)
        except ValueError:
            return {"成功": False, "错误": f"无效状态: {目标状态}"}

        允许的目标 = 状态转换规则.get(当前状态, [])
        if 目标状态枚举 not in 允许的目标:
            return {
                "成功": False,
                "错误": f"不允许从 {当前状态.value} 转换到 {目标状态}",
            }

        旧状态 = 卡片.状态
        卡片.状态 = 目标状态
        卡片.更新时间 = datetime.now().isoformat()

        if 目标状态 == "done":
            卡片.完成时间 = datetime.now().isoformat()

        if 目标状态 == "review":
            卡片.等待审批 = True
        else:
            卡片.等待审批 = False

        转换记录 = 状态转换记录(
            ID=f"trans-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            卡片ID=卡片ID,
            从状态=旧状态,
            到状态=目标状态,
            触发者=触发者,
            原因=原因,
        )
        self.转换历史.append(转换记录)

        return {"成功": True, "卡片": 卡片, "转换记录": 转换记录}

    def 更新卡片(self, 卡片ID: str, 更新数据: dict) -> Optional[Kanban卡片]:
        """更新卡片字段（不改变状态）"""
        卡片 = self.获取卡片(卡片ID)
        if not 卡片:
            return None

        for 字段, 值 in 更新数据.items():
            if hasattr(卡片, 字段) and 字段 not in ["ID", "状态", "创建时间"]:
                setattr(卡片, 字段, 值)

        卡片.更新时间 = datetime.now().isoformat()
        return 卡片

    def 删除卡片(self, 卡片ID: str) -> bool:
        """删除卡片"""
        if 卡片ID in self.卡片列表:
            del self.卡片列表[卡片ID]
            return True
        return False

    def 获取转换历史(self, 卡片ID: str = None) -> list[状态转换记录]:
        """获取状态转换历史"""
        if 卡片ID:
            return [h for h in self.转换历史 if h.卡片ID == 卡片ID]
        return self.转换历史
