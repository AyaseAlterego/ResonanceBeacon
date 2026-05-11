"""监控指标 - Prometheus集成"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from collections import defaultdict
import logging
import time

logger = logging.getLogger(__name__)

@dataclass
class 指标:
    """指标定义"""
    名称: str
    描述: str
    类型: str  # counter, gauge, histogram
    值: float = 0.0
    标签: dict[str, str] = field(default_factory=dict)
    更新时间: datetime = field(default_factory=datetime.now)

class 监控指标收集器:
    """
    监控指标收集器

    收集和管理Prometheus格式的指标
    """

    def __init__(self):
        self._指标: dict[str, 指标] = {}
        self._计数器: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._仪表盘: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._直方图: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        self._计数器标签: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
        self._仪表盘标签: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)

    def 注册指标(self, 指标定义: 指标):
        """注册指标"""
        self._指标[指标定义.名称] = 指标定义
        logger.debug(f"注册监控指标: {指标定义.名称}")

    def 递增计数器(self, 名称: str, 数值: float = 1.0, 标签: dict[str, str] | None = None):
        """递增计数器"""
        标签键 = str(sorted(标签.items())) if 标签 else ""
        self._计数器[名称][标签键] += 数值
        if 标签:
            self._计数器标签[名称][标签键] = 标签

    def 设置仪表盘(self, 名称: str, 数值: float, 标签: dict[str, str] | None = None):
        """设置仪表盘值"""
        标签键 = str(sorted(标签.items())) if 标签 else ""
        self._仪表盘[名称][标签键] = 数值
        if 标签:
            self._仪表盘标签[名称][标签键] = 标签

    def 记录直方图(self, 名称: str, 数值: float, 标签: dict[str, str] | None = None):
        """记录直方图值"""
        标签键 = str(sorted(标签.items())) if 标签 else ""
        if len(self._直方图[名称][标签键]) > 1000:
            self._直方图[名称][标签键].pop(0)
        self._直方图[名称][标签键].append(数值)

    def 获取指标值(self, 名称: str) -> dict[str, Any]:
        """获取指标当前值"""
        if 名称 in self._计数器:
            return {
                "类型": "counter",
                "值": dict(self._计数器[名称])
            }
        elif 名称 in self._仪表盘:
            return {
                "类型": "gauge",
                "值": dict(self._仪表盘[名称])
            }
        elif 名称 in self._直方图:
            值列表 = {}
            for 标签键, 数据列表 in self._直方图[名称].items():
                值列表[标签键] = {
                    "计数": len(数据列表),
                    "总和": sum(数据列表),
                    "平均": sum(数据列表) / len(数据列表) if 数据列表 else 0,
                    "最小": min(数据列表) if 数据列表 else 0,
                    "最大": max(数据列表) if 数据列表 else 0
                }
            return {"类型": "histogram", "值": 值列表}

        return {"类型": "unknown", "值": {}}

    def 获取所有指标(self) -> dict[str, Any]:
        """获取所有指标"""
        结果 = {}
        for 名称 in self._计数器:
            结果[名称] = self.获取指标值(名称)
        for 名称 in self._仪表盘:
            结果[名称] = self.获取指标值(名称)
        for 名称 in self._直方图:
            结果[名称] = self.获取指标值(名称)
        return 结果

    def 导出Prometheus格式(self) -> str:
        """导出Prometheus格式的指标"""
        输出 = []

        for 名称, 计数器数据 in self._计数器.items():
            输出.append(f"# TYPE {名称} counter")
            输出.append(f"# HELP {名称} {名称} counter")
            for 标签键, 值 in 计数器数据.items():
                标签 = self._计数器标签[名称].get(标签键, {})
                if 标签:
                    标签字符串 = ','.join(f'{k}="{v}"' for k, v in 标签.items())
                    输出.append(f"{名称}{{{标签字符串}}} {值}")
                else:
                    输出.append(f"{名称} {值}")

        for 名称, 仪表盘数据 in self._仪表盘.items():
            输出.append(f"# TYPE {名称} gauge")
            输出.append(f"# HELP {名称} {名称} gauge")
            for 标签键, 值 in 仪表盘数据.items():
                标签 = self._仪表盘标签[名称].get(标签键, {})
                if 标签:
                    标签字符串 = ','.join(f'{k}="{v}"' for k, v in 标签.items())
                    输出.append(f"{名称}{{{标签字符串}}} {值}")
                else:
                    输出.append(f"{名称} {值}")

        return "\n".join(输出)

    def 创建默认指标(self):
        """创建默认的监控指标"""
        默认指标 = [
            指标("hermes_pipelines_total", "流水线总数", "counter"),
            指标("hermes_pipelines_running", "正在运行的流水线", "gauge"),
            指标("hermes_tasks_total", "任务总数", "counter"),
            指标("hermes_tasks_duration_seconds", "任务执行时间", "histogram"),
            指标("hermes_agents_active", "活跃智能体", "gauge"),
            指标("hermes_agent_requests_total", "智能体请求总数", "counter"),
            指标("hermes_agent_errors_total", "智能体错误总数", "counter"),
            指标("hermes_artifacts_total", "制品总数", "counter"),
            指标("hermes_tokens_used_total", "令牌使用总量", "counter"),
            指标("hermes_cost_total_dollars", "总成本（美元）", "counter"),
        ]

        for 指标定义 in 默认指标:
            self.注册指标(指标定义)

        logger.info(f"已创建 {len(默认指标)} 个默认监控指标")
