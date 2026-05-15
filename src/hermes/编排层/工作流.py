"""工作流注册表

定义 Oh My Hermes 的 5 个核心工作流：
1. 新项目启动 (start_new_project)
2. 自主开发循环 (autonomous_dev_loop)
3. 快速修复 (quick_fix)
4. 部署流程 (deploy_workflow)
5. 安全扫描 (security_scan)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class 工作流步骤:
    """工作流中的单个步骤"""
    ID: str
    名称: str
    智能体: str
    动作: str
    超时秒: int = 300
    重试次数: int = 2
    条件: str = ""


@dataclass
class 工作流定义:
    """工作流定义"""
    ID: str
    名称: str
    描述: str
    步骤列表: list[工作流步骤] = field(default_factory=list)
    触发条件: str = "manual"
    创建时间: str = field(default_factory=lambda: datetime.now().isoformat())


class 工作流注册表:
    """工作流注册表
    
    管理所有可用的工作流定义。
    """

    def __init__(self):
        self.工作流列表: dict[str, 工作流定义] = {}
        self._初始化默认工作流()

    def _初始化默认工作流(self):
        """初始化默认的 5 个工作流"""
        self.注册工作流(self._创建新项目启动工作流())
        self.注册工作流(self._创建自主开发循环工作流())
        self.注册工作流(self._创建快速修复工作流())
        self.注册工作流(self._创建部署流程工作流())
        self.注册工作流(self._创建安全扫描工作流())

    def 注册工作流(self, 工作流: 工作流定义):
        """注册工作流"""
        self.工作流列表[工作流.ID] = 工作流

    def 获取工作流(self, 工作流ID: str) -> Optional[工作流定义]:
        """获取工作流定义"""
        return self.工作流列表.get(工作流ID)

    def 获取所有工作流(self) -> list[工作流定义]:
        """获取所有工作流"""
        return list(self.工作流列表.values())

    def _创建新项目启动工作流(self) -> 工作流定义:
        """新项目启动工作流"""
        return 工作流定义(
            ID="start_new_project",
            名称="新项目启动",
            描述="从需求澄清到项目初始化的完整流程",
            触发条件="manual",
            步骤列表=[
                工作流步骤("step1", "澄清需求", "PM智能体", "clarify_requirements", 600),
                工作流步骤("step2", "生成产品简报", "PM智能体", "product_brief", 300),
                工作流步骤("step3", "创建设计文档", "CTO智能体", "design_handoff", 600),
                工作流步骤("step4", "初始化项目", "Dev智能体", "project_init", 300),
                工作流步骤("step5", "创建Kanban卡片", "CTO智能体", "create_kanban", 60),
            ],
        )

    def _创建自主开发循环工作流(self) -> 工作流定义:
        """自主开发循环工作流"""
        return 工作流定义(
            ID="autonomous_dev_loop",
            名称="自主开发循环",
            描述="从Backlog选择到部署的完整自主循环",
            触发条件="scheduled",
            步骤列表=[
                工作流步骤("step1", "扫描新任务", "PM智能体", "scan_issues", 120),
                工作流步骤("step2", "分诊评分", "PM智能体", "triage_score", 60),
                工作流步骤("step3", "选择任务", "CTO智能体", "select_task", 30),
                工作流步骤("step4", "执行开发", "Dev智能体", "implement", 1800),
                工作流步骤("step5", "安全审查", "Security智能体", "security_review", 300),
                工作流步骤("step6", "质量验证", "QA智能体", "quality_check", 300),
                工作流步骤("step7", "推送审批", "CTO智能体", "request_approval", 60),
                工作流步骤("step8", "等待审批", "CTO智能体", "await_approval", 86400),
                工作流步骤("step9", "合并部署", "Ops智能体", "merge_deploy", 600),
            ],
        )

    def _创建快速修复工作流(self) -> 工作流定义:
        """快速修复工作流"""
        return 工作流定义(
            ID="quick_fix",
            名称="快速修复",
            描述="针对单文件问题的快速修复流程",
            触发条件="manual",
            步骤列表=[
                工作流步骤("step1", "分析问题", "Dev智能体", "analyze_issue", 120),
                工作流步骤("step2", "执行修复", "Dev智能体", "quick_fix", 300),
                工作流步骤("step3", "验证修复", "QA智能体", "verify_fix", 120),
                工作流步骤("step4", "创建PR", "Dev智能体", "create_pr", 60),
            ],
        )

    def _创建部署流程工作流(self) -> 工作流定义:
        """部署流程工作流（预留）"""
        return 工作流定义(
            ID="deploy_workflow",
            名称="部署流程",
            描述="应用部署和验证流程",
            触发条件="manual",
            步骤列表=[
                工作流步骤("step1", "预部署检查", "QA智能体", "pre_deploy_check", 120),
                工作流步骤("step2", "执行部署", "Ops智能体", "deploy", 600),
                工作流步骤("step3", "健康检查", "Ops智能体", "health_check", 120),
                工作流步骤("step4", "发送通知", "CTO智能体", "send_notification", 30),
            ],
        )

    def _创建安全扫描工作流(self) -> 工作流定义:
        """安全扫描工作流"""
        return 工作流定义(
            ID="security_scan",
            名称="安全扫描",
            描述="定期安全扫描和漏洞审计",
            触发条件="scheduled",
            步骤列表=[
                工作流步骤("step1", "密钥扫描", "Security智能体", "secret_scan", 120),
                工作流步骤("step2", "OWASP检查", "Security智能体", "owasp_check", 120),
                工作流步骤("step3", "CVE审计", "Security智能体", "cve_audit", 300),
                工作流步骤("step4", "生成报告", "Security智能体", "generate_report", 60),
            ],
        )
