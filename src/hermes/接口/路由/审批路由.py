"""审批路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

from ..存储 import 存储实例
from ...认证.RBAC import 用户, 权限
from ..认证依赖 import 需要权限

logger = logging.getLogger(__name__)
router = APIRouter()


class 审批决策请求(BaseModel):
    决策者: str
    批准: bool
    反馈: str = ""


@router.get("/待处理")
async def 获取待处理审批(当前用户: 用户 = Depends(需要权限(权限.审批_查看))):
    列表 = 存储实例.获取待审批()
    return {"待处理审批列表": [{"ID": a.ID, "流水线ID": a.流水线ID, "内容描述": a.内容描述, "状态": a.状态, "风险级别": a.风险级别, "创建时间": a.创建时间} for a in 列表], "总数": len(列表)}


@router.get("/历史")
async def 获取审批历史(当前用户: 用户 = Depends(需要权限(权限.审批_查看))):
    列表 = 存储实例.获取所有审批()
    return {"审批历史": [{"ID": a.ID, "流水线ID": a.流水线ID, "内容描述": a.内容描述, "状态": a.状态, "决策者": a.请求者, "决策时间": a.创建时间} for a in 列表]}


@router.get("/{approval_id}")
async def 获取审批详情(approval_id: str, 当前用户: 用户 = Depends(需要权限(权限.审批_查看))):
    for a in 存储实例.获取所有审批():
        if a.ID == approval_id:
            return {"ID": a.ID, "流水线ID": a.流水线ID, "内容描述": a.内容描述, "状态": a.状态, "风险级别": a.风险级别, "创建时间": a.创建时间}
    raise HTTPException(status_code=404, detail="审批不存在")


@router.post("/{approval_id}/决策")
async def 提交决策(approval_id: str, 请求: 审批决策请求, 当前用户: 用户 = Depends(需要权限(权限.审批_决策))):
    for a in 存储实例.获取所有审批():
        if a.ID == approval_id:
            a.状态 = "approved" if 请求.批准 else "rejected"
            return {"ID": approval_id, "状态": a.状态, "消息": "已批准" if 请求.批准 else "已拒绝"}
    raise HTTPException(status_code=404, detail="审批不存在")
