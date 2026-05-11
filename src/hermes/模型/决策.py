"""决策数据模型"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from ..数据库 import Base

class 决策类型(str, Enum):
    """决策类型枚举"""
    审批 = "approval"
    变更请求 = "change_request"
    冲突解决 = "conflict_resolution"

class 决策状态(str, Enum):
    """决策状态枚举"""
    待处理 = "pending"
    已批准 = "approved"
    已拒绝 = "rejected"
    已超时 = "timeout"

class 决策(Base):
    """决策模型"""
    __tablename__ = "决策"
    __table_args__ = (
        Index("idx_决策_流水线ID", "流水线ID"),
        Index("idx_决策_阶段ID", "阶段ID"),
        Index("idx_决策_状态", "状态"),
    )

    ID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    流水线ID = Column(UUID(as_uuid=True), ForeignKey("流水线.ID"), nullable=False)
    阶段ID = Column(UUID(as_uuid=True), ForeignKey("阶段.ID"), nullable=False)

    决策类型 = Column(SQLEnum(决策类型), nullable=False)
    状态 = Column(SQLEnum(决策状态), default=决策状态.待处理, nullable=False)

    请求者 = Column(String(255), nullable=False)  # 请求者ID或名称
    决策者 = Column(String(255), nullable=True)   # 决策者ID或名称
    决策时间 = Column(DateTime, nullable=True)

    上下文 = Column(JSON, nullable=True, default=dict)  # 决策上下文（制品、代码等）
    反馈 = Column(Text, nullable=True)  # 决策反馈

    创建时间 = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    超时时间 = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<决策 {self.ID} ({self.状态.value})>"
