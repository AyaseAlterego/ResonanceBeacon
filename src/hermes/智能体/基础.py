"""智能体基础接口和数据结构"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

class 智能体类别(str, Enum):
    """智能体类别枚举"""
    探索 = "exploration"
    专家 = "specialist"
    顾问 = "advisor"
    工具 = "utility"
    快速 = "quick"
    深度 = "deep"
    超级大脑 = "ultrabrain"
    视觉工程 = "visual-engineering"

class 智能体成本(str, Enum):
    """智能体成本层级"""
    免费 = "FREE"
    便宜 = "CHEAP"
    昂贵 = "EXPENSIVE"

class 智能体健康状态(str, Enum):
    """智能体健康状态"""
    健康 = "healthy"
    降级 = "degraded"
    不健康 = "unhealthy"

@dataclass
class 智能体能力:
    """智能体能力描述"""
    名称: str
    语言列表: list[str] = field(default_factory=list)
    上下文窗口: int = 200000
    每千令牌成本: float = 0.0
    最大并发任务数: int = 5

@dataclass
class 任务结果:
    """任务执行结果"""
    任务ID: str
    状态: str  # "completed", "failed", "cancelled"
    输出数据: dict[str, Any] = field(default_factory=dict)
    制品列表: list[dict[str, Any]] = field(default_factory=list)
    使用的令牌数: int = 0
    成本: float = 0.0
    耗时毫秒: int = 0
    错误: Optional[str] = None

@dataclass
class 任务需求:
    """任务需求描述，用于智能体选择"""
    能力列表: list[str] = field(default_factory=list)
    预估令牌数: int = 0
    所需语言: Optional[str] = None
    优先级: int = 0  # 0-10，10最高

@dataclass
class 上下文包:
    """传递给智能体的上下文"""
    流水线ID: str = ""
    阶段ID: str = ""
    任务ID: str = ""
    输入数据: dict[str, Any] = field(default_factory=dict)
    之前的制品: list[dict[str, Any]] = field(default_factory=list)
    元数据: dict[str, Any] = field(default_factory=dict)

class 智能体适配器(ABC):
    """
    智能体适配器抽象基类

    所有智能体（Claude Code, OpenCode, Codex等）都必须实现这个接口
    """

    @property
    @abstractmethod
    def 智能体ID(self) -> str:
        """智能体唯一标识"""
        pass

    @property
    @abstractmethod
    def 能力列表(self) -> list[智能体能力]:
        """智能体能力列表"""
        pass

    @property
    @abstractmethod
    def 类别(self) -> 智能体类别:
        """智能体主要类别"""
        pass

    @property
    @abstractmethod
    def 成本层级(self) -> 智能体成本:
        """成本层级"""
        pass

    @abstractmethod
    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化智能体"""
        pass

    @abstractmethod
    async def 健康检查(self) -> bool:
        """执行健康检查"""
        pass

    @abstractmethod
    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        """执行单个任务"""
        pass

    @abstractmethod
    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行任务，返回增量结果"""
        pass

    @abstractmethod
    async def 取消任务(self, 任务ID: str) -> bool:
        """取消正在执行的任务"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.智能体ID} category={self.类别.value}>"

class 智能体工厂(ABC):
    """智能体工厂抽象基类"""

    @property
    @abstractmethod
    def 智能体ID(self) -> str:
        """工厂创建的智能体ID"""
        pass

    @abstractmethod
    def 创建(self, 模型: str, 配置: dict[str, Any]) -> 智能体适配器:
        """创建智能体适配器实例"""
        pass

def 安全创建适配器(
    工厂: 智能体工厂,
    模型: str,
    配置: dict[str, Any]
) -> Optional[智能体适配器]:
    """
    安全创建智能体适配器

    特性：
    1. 捕获所有异常，返回None而不是崩溃
    2. 记录详细的错误日志
    3. 用于优雅降级：一个智能体失败不影响其他智能体
    """
    try:
        适配器 = 工厂.创建(模型=模型, 配置=配置)
        logger.info(f"成功创建智能体适配器: {适配器.智能体ID}")
        return 适配器
    except Exception as e:
        logger.error(
            f"从工厂 {工厂.__name__} 创建智能体适配器失败: {e}",
            exc_info=True
        )
        return None
