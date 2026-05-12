"""流水线路由"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Optional
import logging

from src.hermes.认证.RBAC import 用户, 权限
from src.hermes.接口.认证依赖 import 需要权限
from ..存储 import 存储实例

logger = logging.getLogger(__name__)
router = APIRouter()

class 流水线创建请求(BaseModel):
    """流水线创建请求"""
    名称: str
    描述: str = ""
    流水线定义: dict[str, Any]
    类别: str | None = None

class 流水线运行请求(BaseModel):
    """流水线运行请求"""
    流水线ID: str
    用户输入: str = ""

class 流水线响应(BaseModel):
    """流水线响应"""
    ID: str
    名称: str
    状态: str
    阶段数: int = 0
    完成阶段数: int = 0

class 流水线列表响应(BaseModel):
    """流水线列表响应"""
    流水线列表: list[流水线响应]
    总数: int

@router.get("/", response_model=流水线列表响应)
async def 获取流水线列表(当前用户: 用户 = Depends(需要权限(权限.流水线_读取))):
    列表 = 存储实例.获取所有流水线()
    return 流水线列表响应(
        流水线列表=[流水线响应(ID=p.ID, 名称=p.名称, 状态=p.状态, 阶段数=p.阶段数, 完成阶段数=p.完成阶段数) for p in 列表],
        总数=len(列表)
    )

@router.post("/", response_model=流水线响应, status_code=201)
async def 创建流水线(请求: 流水线创建请求, 当前用户: 用户 = Depends(需要权限(权限.流水线_创建))):
    p = 存储实例.创建流水线(请求.名称, 请求.描述)
    logger.info(f"创建流水线: {p.ID}")
    return 流水线响应(ID=p.ID, 名称=p.名称, 状态=p.状态)

@router.get("/{pipeline_id}", response_model=流水线响应)
async def 获取流水线(pipeline_id: str, 当前用户: 用户 = Depends(需要权限(权限.流水线_读取))):
    p = 存储实例.获取流水线(pipeline_id)
    if not p:
        raise HTTPException(status_code=404, detail="流水线不存在")
    return 流水线响应(ID=p.ID, 名称=p.名称, 状态=p.状态, 阶段数=p.阶段数, 完成阶段数=p.完成阶段数)

@router.post("/{pipeline_id}/运行")
async def 运行流水线(pipeline_id: str, 请求: 流水线运行请求, 当前用户: 用户 = Depends(需要权限(权限.流水线_运行))):
    p = 存储实例.获取流水线(pipeline_id)
    if not p:
        raise HTTPException(status_code=404, detail="流水线不存在")
    p.状态 = "running"
    logger.info(f"运行流水线: {pipeline_id}")
    return {"流水线ID": pipeline_id, "状态": "running", "消息": "流水线已启动"}

@router.post("/{pipeline_id}/取消")
async def 取消流水线(pipeline_id: str, 当前用户: 用户 = Depends(需要权限(权限.流水线_取消))):
    p = 存储实例.获取流水线(pipeline_id)
    if not p:
        raise HTTPException(status_code=404, detail="流水线不存在")
    p.状态 = "cancelled"
    logger.info(f"取消流水线: {pipeline_id}")
    return {"流水线ID": pipeline_id, "状态": "cancelled"}

@router.get("/{pipeline_id}/阶段")
async def 获取阶段列表(pipeline_id: str, 当前用户: 用户 = Depends(需要权限(权限.流水线_读取))):
    """获取流水线的所有阶段"""
    return {"流水线ID": pipeline_id, "阶段列表": []}

@router.get("/{pipeline_id}/制品")
async def 获取制品列表(pipeline_id: str, 当前用户: 用户 = Depends(需要权限(权限.流水线_读取))):
    """获取流水线的所有制品"""
    return {"流水线ID": pipeline_id, "制品列表": []}
