"""数据库连接和会话管理"""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

engine: AsyncEngine | None = None

def 获取引擎() -> AsyncEngine:
    global engine
    if engine is None:
        数据库URL = os.getenv("DATABASE_URL")
        if not 数据库URL:
            raise ValueError("环境变量 DATABASE_URL 未设置")
        engine = create_async_engine(
            数据库URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return engine

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    获取引擎(),
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

# 初始化数据库
async def 初始化数据库():
    async with 获取引擎().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
