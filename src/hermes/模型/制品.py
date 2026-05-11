"""制品数据模型"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from ..数据库 import Base

class 制品类型(str, Enum):
    """制品类型枚举"""
    代码 = "code"
    文档 = "document"
    配置 = "config"
    测试报告 = "test_report"
    审查报告 = "review_report"
    架构文档 = "architecture_doc"
    需求文档 = "requirements_doc"
    API规范 = "api_spec"

class 制品(Base):
    """制品模型"""
    __tablename__ = "制品"
    __table_args__ = (
        Index("idx_制品_流水线ID", "流水线ID"),
        Index("idx_制品_阶段ID", "阶段ID"),
        Index("idx_制品_任务ID", "任务ID"),
        Index("idx_制品_制品类型", "制品类型"),
    )

    ID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    流水线ID = Column(UUID(as_uuid=True), ForeignKey("流水线.ID"), nullable=False)
    阶段ID = Column(UUID(as_uuid=True), ForeignKey("阶段.ID"), nullable=True)
    任务ID = Column(UUID(as_uuid=True), ForeignKey("任务.ID"), nullable=True)

    制品类型 = Column(SQLEnum(制品类型), nullable=False)
    名称 = Column(String(255), nullable=False)
    文件路径 = Column(String(500), nullable=False)
    内容哈希 = Column(String(64), nullable=True)  # SHA-256
    大小字节 = Column(Integer, default=0)
    MIME类型 = Column(String(100), nullable=True)

    创建时间 = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<制品 {self.名称} ({self.制品类型.value})>"
