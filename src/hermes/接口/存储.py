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


class 内存存储:

    def __init__(self):
        self.流水线列表: dict[str, 流水线记录] = {}
        self.智能体列表: dict[str, 智能体记录] = {}
        self.审批列表: dict[str, 审批记录] = {}
        self.项目列表: dict[str, 项目记录] = {}
        self.对话列表: dict[str, 对话记录] = {}
        self.消息列表: dict[str, list[消息记录]] = {}
        self.制品列表: dict[str, 制品记录] = {}

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


存储实例 = 内存存储()
