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


class 内存存储:

    def __init__(self):
        self.流水线列表: dict[str, 流水线记录] = {}
        self.智能体列表: dict[str, 智能体记录] = {}
        self.审批列表: dict[str, 审批记录] = {}

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


存储实例 = 内存存储()
