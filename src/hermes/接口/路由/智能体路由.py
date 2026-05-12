"""智能体路由"""
from fastapi import APIRouter, Depends, HTTPException
import logging

from ..存储 import 存储实例
from ...认证.RBAC import 用户, 权限
from ..认证依赖 import 需要权限

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def 获取智能体列表(当前用户: 用户 = Depends(需要权限(权限.智能体_查看))):
    列表 = 存储实例.获取所有智能体()
    return {"智能体列表": [{"ID": a.ID, "名称": a.名称, "类别": a.类别, "状态": a.状态, "负载": a.负载} for a in 列表], "总数": len(列表)}


@router.get("/{agent_id}")
async def 获取智能体详情(agent_id: str, 当前用户: 用户 = Depends(需要权限(权限.智能体_查看))):
    a = 存储实例.查找智能体(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return {"ID": a.ID, "名称": a.名称, "类别": a.类别, "状态": a.状态, "负载": a.负载}


@router.get("/{agent_id}/健康检查")
async def 获取智能体健康(agent_id: str, 当前用户: 用户 = Depends(需要权限(权限.智能体_查看))):
    a = 存储实例.查找智能体(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return {"智能体ID": agent_id, "健康": a.是否在线, "消息": "在线" if a.是否在线 else "离线"}


@router.get("/{agent_id}/负载")
async def 获取智能体负载(agent_id: str, 当前用户: 用户 = Depends(需要权限(权限.智能体_查看))):
    a = 存储实例.查找智能体(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return {"智能体ID": agent_id, "当前并发": int(a.负载), "最大并发": 5, "负载率": a.负载 / 5}
