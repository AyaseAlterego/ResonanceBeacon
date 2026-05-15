"""审批路由

支持两种审批模式：
1. 传统审批：流水线审批（保留原有逻辑）
2. 自主循环审批：Kanban 卡片 YES/NO 审批流
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from ..存储 import 存储实例

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/审批", tags=["审批"])

# 自主循环引擎实例（由应用初始化时注入）
自主循环引擎实例 = None


def 设置自主循环引擎实例(实例):
    """设置自主循环引擎实例"""
    global 自主循环引擎实例
    自主循环引擎实例 = 实例


class 审批决策请求(BaseModel):
    决策者: str
    批准: bool
    反馈: str = ""


class YESNO审批请求(BaseModel):
    响应: str  # "YES" or "NO"
    反馈: str = ""


class 待审批卡片(BaseModel):
    ID: str
    项目ID: str
    标题: str
    状态: str
    优先级: str
    消息: str
    创建时间: str


@router.get("/待处理")
async def 获取待处理审批():
    """获取待处理审批列表（传统审批）"""
    列表 = 存储实例.获取待审批()
    return {
        "待处理审批列表": [
            {
                "ID": a.ID,
                "流水线ID": a.流水线ID,
                "内容描述": a.内容描述,
                "状态": a.状态,
                "风险级别": a.风险级别,
                "创建时间": a.创建时间,
            }
            for a in 列表
        ],
        "总数": len(列表),
    }


@router.get("/自主循环/待审批")
async def 获取自主循环待审批():
    """获取自主循环中的待审批卡片"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=500, detail="自主循环引擎未初始化")

    # 从所有项目中获取待审批卡片
    待审批列表 = []

    if 存储实例:
        项目列表 = 存储实例.获取所有项目()
        for 项目 in 项目列表:
            # 这里需要从看板获取待审批卡片
            # 简化处理：返回空列表，实际使用时需要注入看板实例
            pass

    return {"待审批卡片": 待审批列表, "总数": len(待审批列表)}


@router.post("/自主循环/{卡片ID}/审批")
async def 提交YESNO审批(卡片ID: str, 请求: YESNO审批请求):
    """提交 YES/NO 审批响应"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=500, detail="自主循环引擎未初始化")

    响应 = 请求.响应.upper()
    if 响应 not in ["YES", "NO"]:
        raise HTTPException(status_code=400, detail="响应必须是 YES 或 NO")

    自主循环引擎实例.处理审批响应(卡片ID, 响应)

    return {
        "成功": True,
        "卡片ID": 卡片ID,
        "响应": 响应,
        "反馈": 请求.反馈,
    }


@router.get("/历史")
async def 获取审批历史():
    """获取审批历史"""
    列表 = 存储实例.获取所有审批()
    return {
        "审批历史": [
            {
                "ID": a.ID,
                "流水线ID": a.流水线ID,
                "内容描述": a.内容描述,
                "状态": a.状态,
                "决策者": a.请求者,
                "决策时间": a.创建时间,
            }
            for a in 列表
        ]
    }


@router.get("/{approval_id}")
async def 获取审批详情(approval_id: str):
    """获取审批详情"""
    for a in 存储实例.获取所有审批():
        if a.ID == approval_id:
            return {
                "ID": a.ID,
                "流水线ID": a.流水线ID,
                "内容描述": a.内容描述,
                "状态": a.状态,
                "风险级别": a.风险级别,
                "创建时间": a.创建时间,
            }
    raise HTTPException(status_code=404, detail="审批不存在")


@router.post("/{approval_id}/决策")
async def 提交决策(approval_id: str, 请求: 审批决策请求):
    """提交审批决策"""
    for a in 存储实例.获取所有审批():
        if a.ID == approval_id:
            a.状态 = "approved" if 请求.批准 else "rejected"
            return {
                "ID": approval_id,
                "状态": a.状态,
                "消息": "已批准" if 请求.批准 else "已拒绝",
            }
    raise HTTPException(status_code=404, detail="审批不存在")
