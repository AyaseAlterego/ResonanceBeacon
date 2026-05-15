"""自主循环引擎

Oh My Hermes 的核心：定时触发、自动分诊、开发、审查、审批的完整循环。

循环流程：
1. 扫描外部事件（GitHub Issues / 用户消息 / 定时任务）
2. PM 分诊新任务
3. CTO 选择最高优先级任务
4. Dev 执行开发
5. Security 安全审查
6. QA 质量验证
7. 推送审批，等待用户 YES/NO
8. YES → 合并部署；NO → 返回 Dev 迭代
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from enum import Enum


class 循环状态(Enum):
    """自主循环状态"""
    IDLE = "idle"
    SCANNING = "scanning"
    TRIAGING = "triaging"
    SELECTING = "selecting"
    DEVELOPING = "developing"
    REVIEWING_SECURITY = "reviewing_security"
    REVIEWING_QA = "reviewing_qa"
    AWAITING_APPROVAL = "awaiting_approval"
    DEPLOYING = "deploying"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class 循环事件:
    """循环中的事件记录"""
    ID: str
    类型: str
    描述: str
    时间: str = field(default_factory=lambda: datetime.now().isoformat())
    元数据: dict = field(default_factory=dict)


@dataclass
class 自主循环配置:
    """自主循环配置"""
    扫描间隔秒: int = 3600
    最大并发任务: int = 3
    自动审批: bool = False
    启用GitHub集成: bool = False
    GitHub仓库: str = ""
    GitHub令牌: str = ""
    通知渠道: str = "web"


class 自主循环引擎:
    """自主循环引擎
    
    管理完整的自主开发循环。
    """

    def __init__(self, 配置: 自主循环配置 = None):
        self.配置 = 配置 or 自主循环配置()
        self.状态 = 循环状态.IDLE
        self.事件日志: list[循环事件] = []
        self.当前卡片ID: str = ""
        self._定时器: Optional[asyncio.Task] = None
        self._运行中 = False

        self.PM智能体 = None
        self.CTO智能体 = None
        self.Dev智能体 = None
        self.Security智能体 = None
        self.QA智能体 = None
        self.Ops智能体 = None

        self.看板 = None
        self.执行层接口 = None
        self.存储 = None

        self._审批回调: Optional[Callable] = None

    def 注册智能体(self, **智能体):
        """注册6个智能体"""
        self.PM智能体 = 智能体.get("PM智能体")
        self.CTO智能体 = 智能体.get("CTO智能体")
        self.Dev智能体 = 智能体.get("Dev智能体")
        self.Security智能体 = 智能体.get("Security智能体")
        self.QA智能体 = 智能体.get("QA智能体")
        self.Ops智能体 = 智能体.get("Ops智能体")

    def 注册依赖(self, 看板, 执行层接口, 存储):
        """注册依赖组件"""
        self.看板 = 看板
        self.执行层接口 = 执行层接口
        self.存储 = 存储

    def 设置审批回调(self, 回调: Callable):
        """设置审批回调函数"""
        self._审批回调 = 回调

    async def 启动(self):
        """启动自主循环"""
        if self._运行中:
            return

        self._运行中 = True
        self.状态 = 循环状态.IDLE
        self._记录事件("引擎启动", "自主循环引擎已启动")

        self._定时器 = asyncio.create_task(self._循环运行())

    async def 停止(self):
        """停止自主循环"""
        self._运行中 = False
        if self._定时器:
            self._定时器.cancel()
            try:
                await self._定时器
            except asyncio.CancelledError:
                pass
        self.状态 = 循环状态.IDLE
        self._记录事件("引擎停止", "自主循环引擎已停止")

    def 暂停(self):
        """暂停自主循环"""
        self.状态 = 循环状态.PAUSED
        self._记录事件("引擎暂停", "自主循环已暂停")

    def 恢复(self):
        """恢复自主循环"""
        if self._运行中:
            self.状态 = 循环状态.IDLE
            self._记录事件("引擎恢复", "自主循环已恢复")

    async def _循环运行(self):
        """主循环"""
        while self._运行中:
            try:
                if self.状态 == 循环状态.PAUSED:
                    await asyncio.sleep(10)
                    continue

                await self._执行循环()
            except Exception as e:
                self.状态 = 循环状态.ERROR
                self._记录事件("循环错误", str(e))
                await asyncio.sleep(60)

            await asyncio.sleep(self.配置.扫描间隔秒)

    async def _执行循环(self):
        """执行单次循环"""
        项目ID列表 = self._获取活跃项目ID列表()

        for 项目ID in 项目ID列表:
            if not self._运行中:
                break

            await self._处理项目(项目ID)

    async def _处理项目(self, 项目ID: str):
        """处理单个项目的循环"""
        self._记录事件("扫描项目", f"开始处理项目: {项目ID}")
        self.状态 = 循环状态.SCANNING

        待审批卡片 = self._获取待审批卡片(项目ID)
        if 待审批卡片:
            await self._处理审批(待审批卡片)
            return

        看板状态 = self.看板.获取看板状态(项目ID)
        backlog卡片 = 看板状态.get("backlog", [])

        if not backlog卡片:
            return

        self.状态 = 循环状态.SELECTING
        选中卡片 = self.CTO智能体.选择任务(backlog卡片)
        if not 选中卡片:
            return

        self.当前卡片ID = 选中卡片.get("ID")
        self._记录事件("选择任务", f"CTO 选择任务: {选中卡片.get('标题')}")

        await self._执行开发流程(项目ID, 选中卡片)

    async def _执行开发流程(self, 项目ID: str, 卡片: dict):
        """执行完整的开发流程"""
        卡片ID = 卡片.get("ID")

        self.状态 = 循环状态.DEVELOPING
        self.看板.转换状态(卡片ID, "in_progress", "autonomous_loop")
        self._记录事件("开始开发", f"Dev 开始开发: {卡片.get('标题')}")

        开发结果 = self.Dev智能体.执行开发(卡片, self.执行层接口)
        if not 开发结果.get("状态") == "completed":
            self._记录事件("开发失败", f"开发失败: {开发结果}")
            self.看板.转换状态(卡片ID, "backlog", "autonomous_loop", "开发失败")
            return

        self.状态 = 循环状态.REVIEWING_SECURITY
        self._记录事件("安全审查", "Security 开始安全审查")

        PR内容 = {
            "PR编号": 开发结果.get("PR信息", {}).get("编号"),
            "代码变更": 开发结果.get("执行结果", {}).get("代码变更", ""),
            "文件列表": 开发结果.get("执行结果", {}).get("文件列表", []),
        }
        安全结果 = self.Security智能体.安全审查(PR内容)

        if not 安全结果.get("通过"):
            self._记录事件("安全审查失败", f"发现 {安全结果.get('问题数量')} 个安全问题")
            self.看板.转换状态(卡片ID, "in_progress", "autonomous_loop", "安全审查失败")
            return

        self.状态 = 循环状态.REVIEWING_QA
        self._记录事件("质量验证", "QA 开始质量验证")

        验证结果 = self.QA智能体.质量验证(PR内容, 安全结果)

        if not 验证结果.get("通过"):
            self._记录事件("质量验证失败", "构建或健康检查失败")
            self.看板.转换状态(卡片ID, "in_progress", "autonomous_loop", "质量验证失败")
            return

        self.状态 = 循环状态.AWAITING_APPROVAL
        self.看板.转换状态(卡片ID, "review", "autonomous_loop")
        self._记录事件("等待审批", "推送审批消息")

        审批消息 = self.QA智能体.生成审批消息(验证结果)
        if self._审批回调:
            self._审批回调(卡片ID, 审批消息)

    async def _处理审批(self, 卡片列表: list):
        """处理待审批的卡片"""
        for 卡片 in 卡片列表:
            if 卡片.get("审批结果") == "approved":
                await self._执行部署(卡片)
            elif 卡片.get("审批结果") == "rejected":
                self.看板.转换状态(卡片.get("ID"), "in_progress", "autonomous_loop", "审批拒绝")
                self._记录事件("审批拒绝", f"卡片 {卡片.get('ID')} 被拒绝")

    async def _执行部署(self, 卡片: dict):
        """执行部署"""
        self.状态 = 循环状态.DEPLOYING
        卡片ID = 卡片.get("ID")

        部署结果 = self.Ops智能体.部署(卡片.get("PR内容", {}), 卡片.get("验证结果", {}))
        监控结果 = self.Ops智能体.健康监控(部署结果)

        报告 = self.Ops智能体.生成部署报告(部署结果, 监控结果)
        self._记录事件("部署完成", 报告)

        self.看板.转换状态(卡片ID, "done", "autonomous_loop")
        self.状态 = 循环状态.IDLE

    def _获取活跃项目ID列表(self) -> list[str]:
        """获取活跃项目ID列表"""
        if self.存储:
            项目列表 = self.存储.获取所有项目()
            return [p.ID for p in 项目列表 if p.阶段 != "完成"]
        return []

    def _获取待审批卡片(self, 项目ID: str) -> list[dict]:
        """获取待审批的卡片"""
        if not self.看板:
            return []

        看板状态 = self.看板.获取看板状态(项目ID)
        review卡片 = 看板状态.get("review", [])

        return [
            {
                "ID": c.ID,
                "标题": c.标题,
                "等待审批": c.等待审批,
                "审批结果": c.元数据.get("审批结果"),
                "PR内容": c.元数据.get("PR内容", {}),
                "验证结果": c.元数据.get("验证结果", {}),
            }
            for c in review卡片
            if c.等待审批
        ]

    def 处理审批响应(self, 卡片ID: str, 响应: str):
        """处理用户的审批响应（YES/NO）"""
        卡片 = self.看板.获取卡片(卡片ID)
        if not 卡片:
            return

        卡片.元数据["审批结果"] = "approved" if 响应.upper() == "YES" else "rejected"
        卡片.元数据["审批时间"] = datetime.now().isoformat()
        卡片.等待审批 = False

        self._记录事件("审批响应", f"卡片 {卡片ID}: {响应}")

    def _记录事件(self, 类型: str, 描述: str, 元数据: dict = None):
        """记录循环事件"""
        事件 = 循环事件(
            ID=f"event-{uuid.uuid4().hex[:8]}",
            类型=类型,
            描述=描述,
            元数据=元数据 or {},
        )
        self.事件日志.append(事件)

    def 获取事件日志(self, 限制: int = 50) -> list[循环事件]:
        """获取事件日志"""
        return self.事件日志[-限制:]

    def 获取状态(self) -> dict:
        """获取引擎状态"""
        return {
            "状态": self.状态.value,
            "运行中": self._运行中,
            "当前卡片ID": self.当前卡片ID,
            "事件数量": len(self.事件日志),
            "配置": {
                "扫描间隔秒": self.配置.扫描间隔秒,
                "自动审批": self.配置.自动审批,
            },
        }
