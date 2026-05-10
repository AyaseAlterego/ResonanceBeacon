"""钩子基础定义"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

class 钩子层级(Enum):
    """钩子层级枚举"""
    会话 = "session"           # 生命周期事件，恢复，通知
    工具守护 = "tool_guard"     # 工具执行前后守护
    转换 = "transform"         # 消息/上下文变换
    继续 = "continuation"       # 循环管理，重试
    技能 = "skill"              # 技能生命周期

class 钩子事件(Enum):
    """钩子事件枚举"""
    # 流水线事件
    流水线已启动 = "pipeline_started"
    流水线已完成 = "pipeline_completed"
    流水线已失败 = "pipeline_failed"
    流水线已取消 = "pipeline_cancelled"

    # 阶段事件
    阶段已开始 = "stage_started"
    阶段已完成 = "stage_completed"
    阶段已失败 = "stage_failed"

    # 任务事件
    任务已开始 = "task_started"
    任务已完成 = "task_completed"
    任务已失败 = "task_failed"
    任务已重试 = "task_retried"

    # 审批事件
    审批已请求 = "approval_requested"
    审批已批准 = "approval_approved"
    审批已拒绝 = "approval_rejected"

    # 智能体事件
    智能体已选择 = "agent_selected"
    智能体执行开始 = "agent_execution_started"
    智能体执行完成 = "agent_execution_completed"
    智能体执行失败 = "agent_execution_failed"

    # 错误事件
    错误已发生 = "error_occurred"
    错误已恢复 = "error_recovered"

@dataclass
class 钩子:
    """钩子定义"""
    名称: str
    层级: 钩子层级
    事件: 钩子事件
    回调: Callable[..., Any]
    优先级: int = 0  # 0-10，10最高
    描述: str = ""

@dataclass
class 钩子上下文:
    """钩子上下文，传递给钩子回调"""
    流水线: Any = None  # 流水线对象
    阶段: Any = None    # 阶段对象
    任务: Any = None    # 任务对象
    智能体: Any = None  # 智能体对象
    结果: Any = None    # 执行结果
    错误: Optional[Exception] = None  # 错误信息
    元数据: dict[str, Any] = field(default_factory=dict)

def 安全创建钩子(
    名称: str,
    工厂: Callable[[钩子上下文], Optional[钩子]],
    上下文: 钩子上下文
) -> Optional[钩子]:
    """
    安全创建钩子

    特性：
    1. 捕获所有异常，返回None而不是崩溃
    2. 记录详细的错误日志
    3. 用于优雅降级：一个钩子失败不影响其他钩子
    """
    try:
        钩子实例 = 工厂(上下文)
        if 钩子实例:
            logger.debug(f"成功创建钩子: {名称}")
        return 钩子实例
    except Exception as e:
        logger.error(f"创建钩子 '{名称}' 失败: {e}", exc_info=True)
        return None
