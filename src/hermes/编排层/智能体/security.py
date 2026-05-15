"""Security 智能体 - 安全官

职责：
- 密钥扫描（防止敏感信息泄露）
- OWASP 安全检查
- CVE 漏洞审计
- 供应链安全检查

Kanban 列：review（在 Dev 和 QA 之间）
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re


@dataclass
class Security智能体:
    """Security 智能体 - 安全官"""

    ID: str = "agent-security"
    名称: str = "Security"
    角色: str = "security"
    描述: str = "安全审查：密钥扫描、OWASP、CVE审计"
    Kanban列: list[str] = field(default_factory=lambda: ["review"])
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())

    密钥模式 = [
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI Secret Key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Token"),
        (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "Private Key"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Password"),
        (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "API Key"),
    ]

    def 安全审查(self, PR内容: dict) -> dict:
        """对 PR 内容进行安全审查
        
        返回审查结果，包含发现的问题和建议
        """
        代码变更 = PR内容.get("代码变更", "")
        文件列表 = PR内容.get("文件列表", [])

        问题列表 = []

        密钥问题 = self._扫描密钥(代码变更)
        if 密钥问题:
            问题列表.extend(密钥问题)

        OWASP问题 = self._OWASP检查(代码变更, 文件列表)
        if OWASP问题:
            问题列表.extend(OWASP问题)

        CVE问题 = self._CVE审计(文件列表)
        if CVE问题:
            问题列表.extend(CVE问题)

        严重级别 = self._计算严重级别(问题列表)

        return {
            "审查ID": f"sec-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "PR编号": PR内容.get("PR编号"),
            "问题列表": 问题列表,
            "问题数量": len(问题列表),
            "严重级别": 严重级别,
            "通过": len(问题列表) == 0 or 严重级别 == "low",
            "审查时间": datetime.now().isoformat(),
        }

    def _扫描密钥(self, 代码: str) -> list[dict]:
        """扫描代码中的密钥和敏感信息"""
        问题 = []

        for 模式, 类型 in self.密钥模式:
            匹配项 = re.finditer(模式, 代码, re.IGNORECASE)
            for 匹配 in 匹配项:
                问题.append({
                    "类型": "密钥泄露",
                    "严重级别": "critical",
                    "描述": f"发现 {类型}",
                    "位置": f"第 {代码[:匹配.start()].count(chr(10)) + 1} 行",
                    "建议": "立即移除并提交新的密钥",
                })

        return 问题

    def _OWASP检查(self, 代码: str, 文件列表: list[str]) -> list[dict]:
        """OWASP Top 10 安全检查"""
        问题 = []

        OWASP模式 = [
            (r"eval\s*\(", "代码注入风险 - eval() 使用", "high"),
            (r"innerHTML\s*=", "XSS 风险 - innerHTML 使用", "medium"),
            (r"document\.write\s*\(", "XSS 风险 - document.write 使用", "medium"),
            (r"SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\+", "SQL 注入风险", "critical"),
            (r"os\.system\s*\(", "命令注入风险 - os.system 使用", "high"),
            (r"subprocess\.call\s*\(.*shell\s*=\s*True", "命令注入风险 - shell=True", "high"),
        ]

        for 模式, 描述, 级别 in OWASP模式:
            if re.search(模式, 代码, re.IGNORECASE):
                问题.append({
                    "类型": "OWASP",
                    "严重级别": 级别,
                    "描述": 描述,
                    "位置": "代码变更中",
                    "建议": f"修复 {描述}",
                })

        return 问题

    def _CVE审计(self, 文件列表: list[str]) -> list[dict]:
        """依赖包 CVE 审计（简化版）"""
        问题 = []

        包文件 = [f for f in 文件列表 if f in ["package.json", "requirements.txt", "pyproject.toml"]]

        if 包文件:
            问题.append({
                "类型": "CVE审计",
                "严重级别": "info",
                "描述": f"检测到依赖文件变更: {', '.join(包文件)}",
                "位置": ", ".join(包文件),
                "建议": "运行 npm audit 或 pip-audit 检查已知漏洞",
            })

        return 问题

    def _计算严重级别(self, 问题列表: list[dict]) -> str:
        """计算整体严重级别"""
        if not 问题列表:
            return "none"

        级别映射 = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        最高级别 = max(问题列表, key=lambda p: 级别映射.get(p.get("严重级别", "low"), 0))

        return 最高级别.get("严重级别", "low")
