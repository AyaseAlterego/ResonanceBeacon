"""Dev 智能体 - 开发者

职责：
- 执行开发任务
- 选择合适的执行引擎（Claude Code / OpenCode / Codex）
- 创建 PR
- 更新 Kanban 状态

Kanban 列：in_progress
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Dev智能体:
    """Dev 智能体 - 开发者"""

    ID: str = "agent-dev"
    名称: str = "Dev"
    角色: str = "developer"
    描述: str = "执行开发任务，创建 PR"
    Kanban列: list[str] = field(default_factory=lambda: ["in_progress"])
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())

    def 执行开发(self, 卡片: dict, 执行层接口) -> dict:
        """执行开发任务
        
        1. 选择合适的执行引擎
        2. 构建任务上下文（注入 Superpowers 方法论）
        3. 调度执行
        4. 返回执行结果
        """
        卡片ID = 卡片.get("ID")
        标题 = 卡片.get("标题", "")
        描述 = 卡片.get("描述", "")

        引擎 = self._选择引擎(卡片)

        任务上下文 = {
            "卡片ID": 卡片ID,
            "标题": 标题,
            "描述": 描述,
            "引擎": 引擎,
            "方法论注入": self._构建方法论注入(卡片),
        }

        结果 = 执行层接口.执行任务(任务上下文)

        return {
            "卡片ID": 卡片ID,
            "状态": "completed" if 结果.get("成功") else "failed",
            "执行引擎": 引擎,
            "执行结果": 结果,
            "PR信息": 结果.get("PR信息"),
        }

    def _选择引擎(self, 卡片: dict) -> str:
        """根据任务特征选择执行引擎"""
        复杂度 = 卡片.get("复杂度", "medium")
        描述 = 卡片.get("描述", "")

        单文件修复 = len(描述) < 100 and "修复" in 描述
        多文件开发 = 复杂度 in ["medium", "high"]

        if 单文件修复:
            return "codex"
        elif 多文件开发:
            return "opencode"
        else:
            return "claude_code"

    def _构建方法论注入(self, 卡片: dict) -> str:
        """构建 Superpowers 方法论注入"""
        注入 = []

        注入.append("你必须遵循以下开发方法论：")
        注入.append("")
        注入.append("## TDD (测试驱动开发)")
        注入.append("1. RED: 先写一个失败测试")
        注入.append("2. 验证测试失败（MANDATORY，不可跳过）")
        注入.append("3. GREEN: 写最小代码使测试通过")
        注入.append("4. 验证测试通过")
        注入.append("5. REFACTOR: 清理代码")
        注入.append("")
        注入.append("## 代码质量")
        注入.append("- DRY: 不要重复自己")
        注入.append("- YAGNI: 不需要的不要加")
        注入.append("- 频繁提交")

        return "\n".join(注入)

    def 创建PR(self, 执行结果: dict) -> dict:
        """创建 Pull Request"""
        PR信息 = 执行结果.get("PR信息", {})

        return {
            "PR编号": PR信息.get("编号"),
            "标题": PR信息.get("标题", "自动PR"),
            "描述": PR信息.get("描述", ""),
            "分支": PR信息.get("分支"),
            "状态": "open",
        }
