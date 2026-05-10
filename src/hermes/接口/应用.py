"""FastAPI应用入口"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from .路由 import 流水线路由, 智能体路由, 审批路由, 配置路由, 健康路由

logger = logging.getLogger(__name__)

@asynccontextmanager
async def 生命周期(app: FastAPI):
    """应用生命周期管理"""
    logger.info("起源信标服务启动中...")
    yield
    logger.info("起源信标服务关闭中...")

def 创建应用() -> FastAPI:
    """创建FastAPI应用"""
    应用 = FastAPI(
        title="起源信标 API",
        description="智能流水线开发系统 REST API",
        version="0.1.0",
        lifespan=生命周期
    )

    # 注册路由
    应用.include_router(流水线路由.router, prefix="/流水线", tags=["流水线"])
    应用.include_router(智能体路由.router, prefix="/智能体", tags=["智能体"])
    应用.include_router(审批路由.router, prefix="/审批", tags=["审批"])
    应用.include_router(配置路由.router, prefix="/配置", tags=["配置"])
    应用.include_router(健康路由.router, tags=["健康检查"])

    return 应用

应用 = 创建应用()
