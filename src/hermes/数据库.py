"""数据库连接和会话管理"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# 数据库URL（从环境变量读取）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hermes:hermes_dev_password@localhost:5432/hermes_db"
)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 生产环境关闭SQL日志
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 基础模型类
class Base(DeclarativeBase):
    pass

# 依赖注入：获取数据库会话
async def 获取数据库会话() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 初始化数据库
async def 初始化数据库():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
