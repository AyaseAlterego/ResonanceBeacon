"""阶段数据模型"""
import uuid
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from ..数据库 import Base

class 阶段状态(str, Enum):
    """阶段状态枚举"""
    待处理 = "pending"
    运行中 = "running"
    等待审批 = "waiting_approval"
    已完成 = "completed"
    失败 = "failed"

class 阶段类型(str, Enum):
    """阶段类型枚举"""
    顺序 = "sequential"     # 顺序执行
    并发 = "parallel"       # 并发执行
    审批 = "approval"       # 需要审批

class 阶段(Base):
    """阶段模型"""
    __tablename__ = "阶段"
    __table_args__ = (
        Index("idx_阶段_流水线ID", "流水线ID"),
        Index("idx_阶段_状态", "状态"),
    )

    ID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    流水线ID = Column(UUID(as_uuid=True), ForeignKey("流水线.ID"), nullable=False)
    名称 = Column(String(255), nullable=False)
    阶段类型 = Column(SQLEnum(阶段类型), default=阶段类型.顺序, nullable=False)
    类别 = Column(String(50), nullable=True)  # 智能体类别
    状态 = Column(SQLEnum(阶段状态), default=阶段状态.待处理, nullable=False)
    顺序 = Column(Integer, nullable=False, default=0)

    开始时间 = Column(DateTime, nullable=True)
    完成时间 = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<阶段 {self.名称} ({self.状态.value})>"
