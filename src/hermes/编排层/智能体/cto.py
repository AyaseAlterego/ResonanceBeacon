"""CTO 智能体 - 首席技术官

职责：
- 编排所有其他智能体
- 监控 Kanban 看板状态
- 从 Backlog 选择最高优先级任务
- 向用户汇报每日状态
- 协调开发流程

Kanban 列：所有列（全局视野）
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class CTO智能体:
    """CTO 智能体 - 编排者"""

    ID: str = "agent-cto"
    名称: str = "CTO"
    角色: str = "orchestrator"
    描述: str = "编排所有智能体，监控看板，向用户汇报"
    Kanban列: list[str] = field(default_factory=lambda: ["backlog", "in_progress", "review", "done"])
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())

    def 选择任务(self, 看板卡片列表: list) -> Optional[dict]:
        """从 Backlog 中选择最高优先级任务
        
        优先级顺序: critical > high > medium > low
        同优先级按创建时间排序（FIFO）
        """
        if not 看板卡片列表:
            return None

        优先级映射 = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        待选卡片 = [c for c in 看板卡片列表 if c.get("状态") == "backlog"]
        if not 待选卡片:
            return None

        待选卡片.sort(
            key=lambda c: (优先级映射.get(c.get("优先级", "low"), 3), c.get("创建时间", ""))
        )

        return 待选卡片[0]

    def 生成状态报告(self, 看板状态: dict) -> str:
        """生成每日状态报告"""
        报告 = ["# CTO 日报\n"]
        报告.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        报告.append("## 看板概览\n")
        for 列, 卡片列表 in 看板状态.items():
            报告.append(f"- **{列}**: {len(卡片列表)} 个任务")

        报告.append("\n## 进行中\n")
        进行中 = 看板状态.get("in_progress", [])
        if 进行中:
            for 卡片 in 进行中:
                报告.append(f"- {卡片.get('标题', '未知任务')} (优先级: {卡片.get('优先级', 'N/A')})")
        else:
            报告.append("- 无进行中的任务")

        报告.append("\n## 待审批\n")
        待审批 = [c for c in 看板状态.get("review", []) if c.get("等待审批")]
        if 待审批:
            for 卡片 in 待审批:
                报告.append(f"- {卡片.get('标题', '未知任务')} - 请回复 YES/NO")
        else:
            报告.append("- 无待审批任务")

        return "\n".join(报告)

    def 协调开发流程(self, 卡片: dict) -> dict:
        """协调从开发到审查的完整流程
        
        返回流程配置，供自主循环引擎执行
        """
        return {
            "卡片ID": 卡片.get("ID"),
            "流程": [
                {"智能体": "Dev智能体", "动作": "执行开发"},
                {"智能体": "Security智能体", "动作": "安全审查"},
                {"智能体": "QA智能体", "动作": "质量验证"},
                {"智能体": "CTO智能体", "动作": "推送审批"},
            ],
        }
