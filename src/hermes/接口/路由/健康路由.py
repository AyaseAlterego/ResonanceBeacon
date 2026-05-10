"""健康检查路由"""
from fastapi import APIRouter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/健康")
async def 健康检查():
    """服务健康检查"""
    return {
        "状态": "healthy",
        "服务": "起源信标",
        "版本": "0.1.0",
        "时间": datetime.now().isoformat()
    }

@router.get("/就绪")
async def 就绪检查():
    """就绪检查"""
    return {
        "状态": "ready",
        "数据库": "connected",
        "智能体": "available"
    }
