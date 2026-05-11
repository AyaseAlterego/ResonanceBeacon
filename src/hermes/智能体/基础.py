"""智能体基础接口和数据结构"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Callable, Any, Optional
from uuid import uuid4
import logging

from .提示词模板 import 提示词模板管理器

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
    项目路径: str = ""

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

    def _提取制品(self, 内容: str) -> list[dict]:
        制品列表 = []
        在代码块中 = False
        当前代码块 = []
        当前语言 = "unknown"

        for 行 in 内容.split('\n'):
            if 行.startswith('```'):
                if 在代码块中:
                    代码 = '\n'.join(当前代码块)
                    if 代码.strip():
                        制品列表.append({"ID": str(uuid4()), "类型": "code", "语言": 当前语言, "内容": 代码, "路径": f"output_{当前语言}.txt"})
                    当前代码块 = []
                    当前语言 = "unknown"
                else:
                    标识 = 行[3:].strip().split()[0] if len(行) > 3 else ""
                    当前语言 = 标识 if 标识 else "unknown"
                在代码块中 = not 在代码块中
            elif 在代码块中:
                当前代码块.append(行)
            else:
                if 行.strip() and not 当前代码块:
                    制品列表.append({"ID": str(uuid4()), "类型": "text", "语言": "unknown", "内容": 行, "路径": "output.txt"})

        return 制品列表

    def _构建提示词(self, 任务类型: str, 输入数据: dict[str, Any], 上下文: 上下文包) -> str:
        模板名称 = self._提示词管理器.根据任务类型获取模板(任务类型)
        上下文数据 = {
            "需求描述": 输入数据.get("需求", 输入数据.get("description", "")),
            "代码内容": 输入数据.get("代码", 输入数据.get("code", "")),
            "代码语言": 输入数据.get("语言", 输入数据.get("language", "python")),
            "项目上下文": str(上下文.元数据) if 上下文 and 上下文.元数据 else "",
            "文档类型": 输入数据.get("文档类型", "API文档"),
            "内容描述": 输入数据.get("内容", ""),
            "目标受众": 输入数据.get("受众", "开发者"),
            "系统需求": 输入数据.get("系统需求", ""),
            "技术约束": 输入数据.get("技术约束", ""),
            "预期规模": 输入数据.get("预期规模", "中等"),
            "原始需求": 输入数据.get("原始需求", ""),
            "项目背景": 输入数据.get("项目背景", ""),
            "利益相关者": 输入数据.get("利益相关者", ""),
            "测试框架": 输入数据.get("测试框架", "pytest"),
        }
        提示词结果 = self._提示词管理器.生成提示词(模板名称, 上下文数据)
        if 提示词结果:
            return 提示词结果["用户提示词"]
        return self._生成默认提示词(任务类型, 输入数据, 上下文)

    def _生成默认提示词(self, 任务类型: str, 输入数据: dict[str, Any], 上下文: 上下文包) -> str:
        部分 = ["你是一个专业的软件开发助手。"]
        映射 = {
            "code_generation": "请根据需求生成高质量的代码。",
            "code_review": "请审查代码质量并提供改进建议。",
            "test_generation": "请为给定代码生成全面的测试用例。",
            "exploration": "请分析代码库并提供详细的分析报告。",
            "code_explanation": "请详细解释代码的功能和逻辑。",
            "requirements_engineering": "请分析需求并输出结构化文档。",
            "architecture_design": "请设计系统架构。",
        }
        if 任务类型 in 映射:
            部分.append(映射[任务类型])
        if 输入数据:
            部分.append("\n## 输入数据\n")
            for 键, 值 in 输入数据.items():
                部分.append(f"**{键}**: {值}")
        return "\n".join(部分)

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
