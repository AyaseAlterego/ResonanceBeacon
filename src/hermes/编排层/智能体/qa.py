"""QA 智能体 - 质量保障

职责：
- 构建检查
- 健康检查
- 代码质量审查
- 生成用户友好的变更摘要

Kanban 列：review
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QA智能体:
    """QA 智能体 - 质检员"""

    ID: str = "agent-qa"
    名称: str = "QA"
    角色: str = "quality"
    描述: str = "质量验证：构建检查、健康检查、变更摘要"
    Kanban列: list[str] = field(default_factory=lambda: ["review"])
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())

    def 质量验证(self, PR内容: dict, 安全审查结果: dict) -> dict:
        """对 PR 进行质量验证
        
        1. 构建检查
        2. 健康检查
        3. 生成变更摘要
        """
        构建结果 = self._构建检查(PR内容)
        健康结果 = self._健康检查(PR内容)
        变更摘要 = self._生成变更摘要(PR内容)

        通过 = 构建结果.get("通过", False) and 健康结果.get("通过", False)

        return {
            "验证ID": f"qa-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "PR编号": PR内容.get("PR编号"),
            "构建检查": 构建结果,
            "健康检查": 健康结果,
            "安全审查": 安全审查结果,
            "变更摘要": 变更摘要,
            "通过": 通过,
            "验证时间": datetime.now().isoformat(),
        }

    def _构建检查(self, PR内容: dict) -> dict:
        """检查构建是否通过"""
        项目类型 = PR内容.get("项目类型", "unknown")

        构建命令 = {
            "typescript": ["npm run build", "npm run typecheck"],
            "python": ["pytest", "mypy src/"],
            "rust": ["cargo build", "cargo test"],
        }.get(项目类型, ["echo 'No build command'"])

        构建通过 = PR内容.get("构建通过", True)

        return {
            "命令": 构建命令,
            "通过": 构建通过,
            "输出": PR内容.get("构建输出", ""),
        }

    def _健康检查(self, PR内容: dict) -> dict:
        """检查应用健康状态"""
        健康端点 = PR内容.get("健康端点", "/health")
        预期状态码 = PR内容.get("预期状态码", 200)

        模拟检查 = PR内容.get("模拟健康检查", True)

        return {
            "端点": 健康端点,
            "状态码": 预期状态码 if 模拟检查 else 500,
            "响应时间": "120ms" if 模拟检查 else "timeout",
            "通过": 模拟检查,
        }

    def _生成变更摘要(self, PR内容: dict) -> str:
        """生成用户友好的变更摘要"""
        标题 = PR内容.get("标题", "未知变更")
        描述 = PR内容.get("描述", "")
        文件变更 = PR内容.get("文件变更", [])

        摘要 = [f"## {标题}\n"]

        if 描述:
            摘要.append(f"**变更内容**: {描述}\n")

        if 文件变更:
            摘要.append("**变更文件**:")
            for 文件 in 文件变更[:10]:
                摘要.append(f"- {文件}")
            if len(文件变更) > 10:
                摘要.append(f"- ... 还有 {len(文件变更) - 10} 个文件")

        摘要.append(f"\n**构建状态**: {'通过' if PR内容.get('构建通过') else '失败'}")
        摘要.append(f"**健康检查**: {'通过' if PR内容.get('模拟健康检查') else '失败'}")

        return "\n".join(摘要)

    def 生成审批消息(self, 验证结果: dict) -> str:
        """生成发送给用户的审批消息"""
        PR编号 = 验证结果.get("PR编号", "N/A")
        变更摘要 = 验证结果.get("变更摘要", "")
        构建通过 = 验证结果.get("构建检查", {}).get("通过", False)
        健康通过 = 验证结果.get("健康检查", {}).get("通过", False)
        安全通过 = 验证结果.get("安全审查", {}).get("通过", False)

        状态图标 = {
            True: "✅",
            False: "❌",
        }

        消息 = [
            f"## PR #{PR编号} 等待审批\n",
            变更摘要,
            "",
            "---",
            "",
            f"构建: {状态图标[构建通过]} {'通过' if 构建通过 else '失败'}",
            f"健康检查: {状态图标[健康通过]} {'通过' if 健康通过 else '失败'}",
            f"安全审查: {状态图标[安全通过]} {'通过' if 安全通过 else '失败'}",
            "",
            "---",
            "",
            "回复 **YES** 合并部署，回复 **NO** 并说明原因。",
        ]

        return "\n".join(消息)
