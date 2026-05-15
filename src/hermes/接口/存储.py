"""内存数据存储"""
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
from datetime import datetime


@dataclass
class 流水线记录:
    ID: str
    名称: str
    描述: str = ""
    状态: str = "pending"
    阶段数: int = 0
    完成阶段数: int = 0
    创建时间: str = ""


@dataclass
class 智能体记录:
    ID: str
    名称: str
    类别: str
    状态: str = "idle"
    负载: float = 0.0
    是否在线: bool = True


@dataclass
class 审批记录:
    ID: str
    流水线ID: str
    内容描述: str
    状态: str = "pending"
    风险级别: str = "低"
    请求者: str = "system"
    创建时间: str = ""


@dataclass
class 项目记录:
    ID: str
    名称: str
    描述: str = ""
    阶段: str = "需求分析"
    仓库URL: str = ""
    工作目录: str = ""
    配置: dict = field(default_factory=dict)
    创建时间: str = ""
    更新时间: str = ""


@dataclass
class 对话记录:
    ID: str
    项目ID: str
    创建时间: str = ""


@dataclass
class 消息记录:
    ID: str
    对话ID: str
    角色: str
    内容: str
    元数据: dict = field(default_factory=dict)
    创建时间: str = ""


@dataclass
class 制品记录:
    ID: str
    项目ID: str
    制品类型: str
    名称: str
    内容: str
    阶段: str
    技能: str
    文件路径: str = ""
    创建时间: str = ""


@dataclass
class Kanban卡片记录:
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
    创建时间: str = ""
    更新时间: str = ""
    完成时间: str = ""
    元数据: dict = field(default_factory=dict)


@dataclass
class 状态转换记录:
    ID: str
    卡片ID: str
    从状态: str
    到状态: str
    触发者: str
    原因: str = ""
    时间: str = ""


class 内存存储:

    def __init__(self):
        self.流水线列表: dict[str, 流水线记录] = {}
        self.智能体列表: dict[str, 智能体记录] = {}
        self.审批列表: dict[str, 审批记录] = {}
        self.项目列表: dict[str, 项目记录] = {}
        self.对话列表: dict[str, 对话记录] = {}
        self.消息列表: dict[str, list[消息记录]] = {}
        self.制品列表: dict[str, 制品记录] = {}
        self.Kanban卡片列表: dict[str, Kanban卡片记录] = {}
        self.Kanban转换历史: list[状态转换记录] = []

    def 创建流水线(self, 名称: str, 描述: str = "") -> 流水线记录:
        r = 流水线记录(
            ID=f"pl-{uuid4()}",
            名称=名称,
            描述=描述,
            创建时间=datetime.now().isoformat()
        )
        self.流水线列表[r.ID] = r
        return r

    def 获取流水线(self, ID: str) -> 流水线记录 | None:
        return self.流水线列表.get(ID)

    def 获取所有流水线(self) -> list[流水线记录]:
        return list(self.流水线列表.values())

    def 查找智能体(self, ID: str) -> 智能体记录 | None:
        return self.智能体列表.get(ID)

    def 获取所有智能体(self) -> list[智能体记录]:
        return list(self.智能体列表.values())

    def 获取待审批(self) -> list[审批记录]:
        return [a for a in self.审批列表.values() if a.状态 == "pending"]

    def 获取所有审批(self) -> list[审批记录]:
        return list(self.审批列表.values())

    def 添加审批(self, 流水线ID: str, 内容描述: str) -> 审批记录:
        r = 审批记录(
            ID=f"ap-{uuid4()}",
            流水线ID=流水线ID,
            内容描述=内容描述,
            创建时间=datetime.now().isoformat()
        )
        self.审批列表[r.ID] = r
        return r

    def 创建项目(self, 名称: str, 描述: str = "") -> 项目记录:
        now = datetime.now().isoformat()
        r = 项目记录(
            ID=f"proj-{uuid4()}",
            名称=名称,
            描述=描述,
            创建时间=now,
            更新时间=now,
        )
        self.项目列表[r.ID] = r
        对话 = self.创建对话(r.ID)
        return r

    def 获取项目(self, ID: str) -> 项目记录 | None:
        return self.项目列表.get(ID)

    def 获取所有项目(self) -> list[项目记录]:
        return list(self.项目列表.values())

    def 更新项目阶段(self, ID: str, 阶段: str) -> 项目记录 | None:
        项目 = self.项目列表.get(ID)
        if not 项目:
            return None
        项目.阶段 = 阶段
        项目.更新时间 = datetime.now().isoformat()
        return 项目

    def 创建对话(self, 项目ID: str) -> 对话记录:
        r = 对话记录(
            ID=f"conv-{uuid4()}",
            项目ID=项目ID,
            创建时间=datetime.now().isoformat(),
        )
        self.对话列表[r.ID] = r
        return r

    def 获取项目对话(self, 项目ID: str) -> 对话记录 | None:
        for 对话 in self.对话列表.values():
            if 对话.项目ID == 项目ID:
                return 对话
        return None

    def 添加消息(self, 对话ID: str, 角色: str, 内容: str, 元数据: dict | None = None) -> 消息记录:
        r = 消息记录(
            ID=f"msg-{uuid4()}",
            对话ID=对话ID,
            角色=角色,
            内容=内容,
            元数据=元数据 or {},
            创建时间=datetime.now().isoformat(),
        )
        if 对话ID not in self.消息列表:
            self.消息列表[对话ID] = []
        self.消息列表[对话ID].append(r)
        return r

    def 获取对话消息(self, 对话ID: str) -> list[消息记录]:
        return self.消息列表.get(对话ID, [])

    def 创建制品(self, 项目ID: str, 制品类型: str, 名称: str, 内容: str, 阶段: str, 技能: str) -> 制品记录:
        r = 制品记录(
            ID=f"art-{uuid4()}",
            项目ID=项目ID,
            制品类型=制品类型,
            名称=名称,
            内容=内容,
            阶段=阶段,
            技能=技能,
            创建时间=datetime.now().isoformat(),
        )
        self.制品列表[r.ID] = r
        return r

    def 获取项目制品(self, 项目ID: str) -> list[制品记录]:
        return [a for a in self.制品列表.values() if a.项目ID == 项目ID]

    # ====== Kanban 看板 CRUD ======

    def 创建Kanban卡片(self, 数据: dict) -> Kanban卡片记录:
        卡片ID = f"card-{uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        r = Kanban卡片记录(
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
            创建时间=now,
            更新时间=now,
        )
        self.Kanban卡片列表[卡片ID] = r
        return r

    def 获取Kanban卡片(self, 卡片ID: str) -> Kanban卡片记录 | None:
        return self.Kanban卡片列表.get(卡片ID)

    def 获取项目Kanban卡片(self, 项目ID: str) -> list[Kanban卡片记录]:
        return [c for c in self.Kanban卡片列表.values() if c.项目ID == 项目ID]

    def 获取项目看板状态(self, 项目ID: str) -> dict[str, list[Kanban卡片记录]]:
        卡片列表 = self.获取项目Kanban卡片(项目ID)
        return {
            "backlog": [c for c in 卡片列表 if c.状态 == "backlog"],
            "in_progress": [c for c in 卡片列表 if c.状态 == "in_progress"],
            "review": [c for c in 卡片列表 if c.状态 == "review"],
            "done": [c for c in 卡片列表 if c.状态 == "done"],
            "cancelled": [c for c in 卡片列表 if c.状态 == "cancelled"],
        }

    def 转换Kanban卡片状态(self, 卡片ID: str, 目标状态: str, 触发者: str = "system", 原因: str = "") -> dict:
        卡片 = self.获取Kanban卡片(卡片ID)
        if not 卡片:
            return {"成功": False, "错误": "卡片不存在"}

        状态转换规则 = {
            "backlog": ["in_progress", "cancelled"],
            "in_progress": ["review", "backlog"],
            "review": ["done", "in_progress"],
            "done": [],
            "cancelled": [],
        }

        允许的目标 = 状态转换规则.get(卡片.状态, [])
        if 目标状态 not in 允许的目标:
            return {"成功": False, "错误": f"不允许从 {卡片.状态} 转换到 {目标状态}"}

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
            时间=datetime.now().isoformat(),
        )
        self.Kanban转换历史.append(转换记录)

        return {"成功": True, "卡片": 卡片, "转换记录": 转换记录}

    def 更新Kanban卡片(self, 卡片ID: str, 更新数据: dict) -> Kanban卡片记录 | None:
        卡片 = self.获取Kanban卡片(卡片ID)
        if not 卡片:
            return None

        for 字段, 值 in 更新数据.items():
            if hasattr(卡片, 字段) and 字段 not in ["ID", "状态", "创建时间"]:
                setattr(卡片, 字段, 值)

        卡片.更新时间 = datetime.now().isoformat()
        return 卡片

    def 删除Kanban卡片(self, 卡片ID: str) -> bool:
        if 卡片ID in self.Kanban卡片列表:
            del self.Kanban卡片列表[卡片ID]
            return True
        return False

    def 获取Kanban转换历史(self, 卡片ID: str = None) -> list[状态转换记录]:
        if 卡片ID:
            return [h for h in self.Kanban转换历史 if h.卡片ID == 卡片ID]
        return self.Kanban转换历史


存储实例 = 内存存储()
