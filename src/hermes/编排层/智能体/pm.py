"""PM 智能体 - 产品经理

职责：
- 分诊 GitHub Issues 和用户请求
- 评分和优先级排序
- 创建 Kanban 卡片
- 管理 Backlog

Kanban 列：backlog
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PM智能体:
    """PM 智能体 - 分诊员"""

    ID: str = "agent-pm"
    名称: str = "PM"
    角色: str = "triage"
    描述: str = "分诊任务，评分优先级，管理 Backlog"
    Kanban列: list[str] = field(default_factory=lambda: ["backlog"])
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())

    def 分诊任务(self, 原始输入: dict) -> dict:
        """对原始任务输入进行分诊
        
        分析任务类型、复杂度、优先级
        返回结构化的卡片数据
        """
        标题 = 原始输入.get("标题", "未命名任务")
        描述 = 原始输入.get("描述", "")
        来源 = 原始输入.get("来源", "manual")

        复杂度 = self._评估复杂度(描述)
        优先级 = self._评估优先级(原始输入)
        预估工时 = self._预估工时(复杂度)

        return {
            "标题": 标题,
            "描述": 描述,
            "来源": 来源,
            "复杂度": 复杂度,
            "优先级": 优先级,
            "预估工时": 预估工时,
            "状态": "backlog",
            "负责人": "dev",
            "创建时间": datetime.now().isoformat(),
        }

    def _评估复杂度(self, 描述: str) -> str:
        """评估任务复杂度"""
        if not 描述:
            return "low"

        描述长度 = len(描述)
        关键词 = ["架构", "重构", "迁移", "集成", "优化"]

        if 描述长度 > 500 or any(kw in 描述 for kw in 关键词):
            return "high"
        elif 描述长度 > 200:
            return "medium"
        else:
            return "low"

    def _评估优先级(self, 输入: dict) -> str:
        """评估任务优先级"""
        标记优先级 = 输入.get("优先级", "")
        if 标记优先级 in ["critical", "high", "medium", "low"]:
            return 标记优先级

        标题 = 输入.get("标题", "").lower()
        if any(kw in 标题 for kw in ["bug", "崩溃", "安全", "漏洞", "紧急"]):
            return "critical"
        elif any(kw in 标题 for kw in ["修复", "错误", "问题"]):
            return "high"
        else:
            return "medium"

    def _预估工时(self, 复杂度: str) -> str:
        """根据复杂度预估工时"""
        工时映射 = {"low": "1-2小时", "medium": "半天", "high": "1-2天"}
        return 工时映射.get(复杂度, "未知")

    def 批量分诊(self, 任务列表: list[dict]) -> list[dict]:
        """批量分诊多个任务"""
        return [self.分诊任务(任务) for 任务 in 任务列表]
