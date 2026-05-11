"""Pydantic配置模式定义"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

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

class 智能体配置(BaseModel):
    """单个智能体配置"""
    模型: str = Field(default="claude-3-5-sonnet-20241022", description="使用的模型")
    最大令牌数: int = Field(default=4096, description="最大令牌数")
    温度: float = Field(default=0.3, ge=0, le=1, description="生成温度")
    上下文窗口: int = Field(default=200000, description="上下文窗口大小")
    每千令牌成本: float = Field(default=0.0, description="每千令牌成本")
    最大并发数: int = Field(default=5, description="最大并发任务数")

class 类别配置(BaseModel):
    """类别配置，定义类别的默认设置"""
    模型: Optional[str] = Field(default=None, description="类别默认模型")
    温度: Optional[float] = Field(default=None, description="类别默认温度")
    描述: str = Field(default="", description="类别描述")
    智能体优先级: list[str] = Field(default_factory=list, description="智能体优先级列表")

class 流水线配置(BaseModel):
    """流水线默认配置"""
    最大重试次数: int = Field(default=3, description="最大重试次数")
    退避乘数: float = Field(default=2.0, description="退避乘数")
    初始延迟秒数: int = Field(default=30, description="初始延迟秒数")
    任务超时: int = Field(default=600, description="单任务超时（秒）")
    阶段超时: int = Field(default=3600, description="阶段超时（秒）")
    流水线超时: int = Field(default=86400, description="流水线超时（秒）")
    测试覆盖率最低值: float = Field(default=0.80, description="最低测试覆盖率")
    最大lint错误数: int = Field(default=0, description="最大lint错误数")
    最大安全关键问题数: int = Field(default=0, description="最大安全关键问题数")

class 后台任务配置(BaseModel):
    """后台任务配置"""
    每智能体最大并发数: int = Field(default=5, description="每智能体最大并发数")
    熔断器阈值: int = Field(default=5, description="熔断器失败阈值")
    熔断器恢复时间: int = Field(default=60, description="熔断器恢复时间（秒）")
    任务超时: int = Field(default=600, description="任务超时（秒）")
    轮询间隔: int = Field(default=3, description="轮询间隔（秒）")

class 禁用列表配置(BaseModel):
    """禁用的组件列表"""
    智能体: list[str] = Field(default_factory=list, description="禁用的智能体")
    钩子: list[str] = Field(default_factory=list, description="禁用的钩子")
    工具: list[str] = Field(default_factory=list, description="禁用的工具")
    命令: list[str] = Field(default_factory=list, description="禁用的命令")

class 应用配置(BaseModel):
    """应用主配置"""
    # 项目元数据
    项目名称: str = Field(default="起源信标", description="项目名称")
    版本: str = Field(default="0.1.0", description="版本号")
    环境: str = Field(default="development", description="环境（development/production）")

    # 智能体配置
    智能体: dict[str, 智能体配置] = Field(default_factory=lambda: {
        "claude_code": 智能体配置(),
        "opencode": 智能体配置(模型="gpt-4o"),
        "codex": 智能体配置(模型="codex-mini"),
    }, description="智能体配置")

    # 类别配置
    类别: dict[str, 类别配置] = Field(default_factory=lambda: {
        "ultrabrain": 类别配置(描述="架构级，高难度逻辑", 智能体优先级=["claude_code"]),
        "deep": 类别配置(描述="深度思考的复杂任务", 智能体优先级=["claude_code", "opencode"]),
        "quick": 类别配置(描述="小改动，快速修复", 智能体优先级=["claude_code", "opencode"]),
        "visual-engineering": 类别配置(描述="前端/UI/UX", 智能体优先级=["claude_code"]),
        "specialist": 类别配置(描述="特定领域专长", 智能体优先级=["claude_code", "codex"]),
        "exploration": 类别配置(描述="代码库分析，需求理解", 智能体优先级=["claude_code", "opencode"]),
        "advisor": 类别配置(描述="审查、架构建议", 智能体优先级=["claude_code"]),
        "utility": 类别配置(描述="测试、文档、配置", 智能体优先级=["claude_code", "opencode", "codex"]),
    }, description="类别配置")

    # 流水线配置
    流水线默认值: 流水线配置 = Field(default_factory=流水线配置, description="流水线默认配置")

    # 后台任务配置
    后台任务: 后台任务配置 = Field(default_factory=后台任务配置, description="后台任务配置")

    # 禁用列表
    禁用的: 禁用列表配置 = Field(default_factory=禁用列表配置, description="禁用的组件")

    # 数据库配置
    数据库URL: str = Field(
        default="",
        description="数据库连接URL"
    )
    RedisURL: str = Field(
        default="",
        description="Redis连接URL"
    )

    class 配置:
        env_prefix = "HERMES_"
        env_file = ".env"
        env_file_encoding = "utf-8"
