"""项目数据模型"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from ..数据库 import Base

class 项目(Base):
    """项目模型"""
    __tablename__ = "项目"

    ID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    名称 = Column(String(255), nullable=False, unique=True)
    描述 = Column(Text, nullable=True)
    仓库URL = Column(String(500), nullable=True)
    配置 = Column(JSON, nullable=True, default=dict)

    创建时间 = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    更新时间 = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<项目 {self.名称}>"
