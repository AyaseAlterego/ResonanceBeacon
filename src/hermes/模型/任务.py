"""任务数据模型"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from ..数据库 import Base

class 任务状态(str, Enum):
    """任务状态枚举"""
    待处理 = "pending"
    运行中 = "running"
    已完成 = "completed"
    失败 = "failed"
    已重试 = "retrying"
    已取消 = "cancelled"

class 任务(Base):
    """任务模型"""
    __tablename__ = "任务"
    __table_args__ = (
        Index("idx_任务_阶段ID", "阶段ID"),
        Index("idx_任务_状态", "状态"),
        Index("idx_任务_类别", "类别"),
    )

    ID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    阶段ID = Column(UUID(as_uuid=True), ForeignKey("阶段.ID"), nullable=False)
    名称 = Column(String(255), nullable=False)
    类别 = Column(String(50), nullable=True)  # 智能体类别
    状态 = Column(SQLEnum(任务状态), default=任务状态.待处理, nullable=False)
    依赖项 = Column(JSON, nullable=True, default=list)  # 依赖的任务ID列表

    # 输入输出
    输入数据 = Column(JSON, nullable=True, default=dict)
    输出数据 = Column(JSON, nullable=True, default=dict)

    # 执行信息
    使用的智能体 = Column(String(100), nullable=True)
    令牌数 = Column(Integer, default=0)
    成本 = Column(Float, default=0.0)
    耗时毫秒 = Column(Integer, default=0)

    # 错误和重试
    错误 = Column(Text, nullable=True)
    重试次数 = Column(Integer, default=0)
    最大重试次数 = Column(Integer, default=3)

    # 时间戳
    开始时间 = Column(DateTime, nullable=True)
    完成时间 = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<任务 {self.名称} ({self.状态.value})>"
