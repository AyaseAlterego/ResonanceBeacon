"""健康检查路由"""
from fastapi import APIRouter
from datetime import datetime
import logging

from ...智能体 import 智能体注册表

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/健康")
@router.get("/健康/健康")
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
    状态 = {"状态": "healthy", "数据库": "disconnected", "智能体": "unknown"}
    try:
        from ...数据库 import 获取数据库会话
        数据库会话 = 获取数据库会话()
        状态["数据库"] = "connected"
    except:
        状态["状态"] = "degraded"

    注册表 = 智能体注册表()
    健康智能体 = 注册表.获取所有健康智能体()
    状态["智能体"] = "available" if len(健康智能体) > 0 else "unavailable"
    if 状态["智能体"] == "unavailable":
        状态["状态"] = "degraded"

    return 状态

@router.get("/设置/默认密钥")
async def 获取默认密钥():
    """获取桌面端默认API密钥"""
    from ..应用 import _LOCAL_API_KEY
    return {"密钥": _LOCAL_API_KEY}
