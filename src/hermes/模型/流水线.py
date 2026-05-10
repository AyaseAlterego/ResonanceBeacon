"""流水线数据模型"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from ..数据库 import Base

class 流水线状态(str, Enum):
    """流水线状态枚举"""
    待处理 = "pending"
    运行中 = "running"
    等待审批 = "waiting_approval"
    已完成 = "completed"
    失败 = "failed"
    已取消 = "cancelled"

class 流水线(Base):
    """流水线模型"""
    __tablename__ = "流水线"
    __table_args__ = (
        Index("idx_流水线_项目ID", "项目ID"),
        Index("idx_流水线_状态", "状态"),
        Index("idx_流水线_创建时间", "创建时间"),
    )

    ID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    项目ID = Column(UUID(as_uuid=True), ForeignKey("项目.ID"), nullable=False)
    名称 = Column(String(255), nullable=False)
    模板名称 = Column(String(255), nullable=True)
    流水线定义 = Column(JSON, nullable=False)  # DAG定义
    状态 = Column(SQLEnum(流水线状态), default=流水线状态.待处理, nullable=False)
    类别 = Column(String(50), nullable=True)  # 智能体类别

    开始时间 = Column(DateTime, nullable=True)
    完成时间 = Column(DateTime, nullable=True)
    创建时间 = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 统计信息
    使用的令牌数 = Column(Integer, default=0)
    总成本 = Column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<流水线 {self.名称} ({self.状态.value})>"
