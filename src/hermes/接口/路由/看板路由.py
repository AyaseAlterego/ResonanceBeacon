"""看板路由

提供 Kanban 看板的 CRUD API。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/看板", tags=["看板"])

# 全局看板状态机（由应用初始化时注入）
看板状态机实例 = None


def 设置看板实例(实例):
    """设置看板状态机实例"""
    global 看板状态机实例
    看板状态机实例 = 实例


class 创建卡片请求(BaseModel):
    项目ID: str
    标题: str
    描述: str = ""
    优先级: str = "medium"
    负责人: str = "dev"
    来源: str = "manual"


class 更新卡片请求(BaseModel):
    标题: Optional[str] = None
    描述: Optional[str] = None
    优先级: Optional[str] = None
    负责人: Optional[str] = None
    元数据: Optional[dict] = None


class 状态转换请求(BaseModel):
    目标状态: str
    原因: str = ""


@router.get("/项目/{项目ID}")
async def 获取项目看板(项目ID: str):
    """获取项目的完整看板状态"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    看板状态 = 看板状态机实例.获取看板状态(项目ID)

    return {
        "项目ID": 项目ID,
        "backlog": [_卡片到字典(c) for c in 看板状态.get("backlog", [])],
        "in_progress": [_卡片到字典(c) for c in 看板状态.get("in_progress", [])],
        "review": [_卡片到字典(c) for c in 看板状态.get("review", [])],
        "done": [_卡片到字典(c) for c in 看板状态.get("done", [])],
        "cancelled": [_卡片到字典(c) for c in 看板状态.get("cancelled", [])],
    }


@router.post("/卡片")
async def 创建卡片(请求: 创建卡片请求):
    """创建新卡片"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    卡片数据 = {
        "项目ID": 请求.项目ID,
        "标题": 请求.标题,
        "描述": 请求.描述,
        "优先级": 请求.优先级,
        "负责人": 请求.负责人,
        "来源": 请求.来源,
    }

    卡片 = 看板状态机实例.创建卡片(卡片数据)
    return _卡片到字典(卡片)


@router.get("/卡片/{卡片ID}")
async def 获取卡片(卡片ID: str):
    """获取卡片详情"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    卡片 = 看板状态机实例.获取卡片(卡片ID)
    if not 卡片:
        raise HTTPException(status_code=404, detail="卡片不存在")

    return _卡片到字典(卡片)


@router.put("/卡片/{卡片ID}")
async def 更新卡片(卡片ID: str, 请求: 更新卡片请求):
    """更新卡片"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    更新数据 = 请求.model_dump(exclude_unset=True)
    卡片 = 看板状态机实例.更新卡片(卡片ID, 更新数据)

    if not 卡片:
        raise HTTPException(status_code=404, detail="卡片不存在")

    return _卡片到字典(卡片)


@router.post("/卡片/{卡片ID}/状态")
async def 转换卡片状态(卡片ID: str, 请求: 状态转换请求):
    """转换卡片状态"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    结果 = 看板状态机实例.转换状态(
        卡片ID,
        请求.目标状态,
        触发者="api",
        原因=请求.原因,
    )

    if not 结果.get("成功"):
        raise HTTPException(status_code=400, detail=结果.get("错误"))

    return {
        "成功": True,
        "卡片": _卡片到字典(结果.get("卡片")),
        "转换记录": {
            "从状态": 结果.get("转换记录").从状态,
            "到状态": 结果.get("转换记录").到状态,
            "时间": 结果.get("转换记录").时间,
        },
    }


@router.delete("/卡片/{卡片ID}")
async def 删除卡片(卡片ID: str):
    """删除卡片"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    成功 = 看板状态机实例.删除卡片(卡片ID)
    if not 成功:
        raise HTTPException(status_code=404, detail="卡片不存在")

    return {"成功": True}


@router.get("/卡片/{卡片ID}/历史")
async def 获取卡片历史(卡片ID: str):
    """获取卡片状态转换历史"""
    if not 看板状态机实例:
        raise HTTPException(status_code=500, detail="看板服务未初始化")

    历史 = 看板状态机实例.获取转换历史(卡片ID)

    return {
        "卡片ID": 卡片ID,
        "历史": [
            {
                "ID": h.ID,
                "从状态": h.从状态,
                "到状态": h.到状态,
                "触发者": h.触发者,
                "原因": h.原因,
                "时间": h.时间,
            }
            for h in 历史
        ],
    }


def _卡片到字典(卡片) -> dict:
    """将 Kanban卡片 转换为字典"""
    return {
        "ID": 卡片.ID,
        "项目ID": 卡片.项目ID,
        "标题": 卡片.标题,
        "描述": 卡片.描述,
        "状态": 卡片.状态,
        "优先级": 卡片.优先级,
        "负责人": 卡片.负责人,
        "来源": 卡片.来源,
        "复杂度": 卡片.复杂度,
        "预估工时": 卡片.预估工时,
        "等待审批": 卡片.等待审批,
        "关联任务ID": 卡片.关联任务ID,
        "关联制品ID列表": 卡片.关联制品ID列表,
        "创建时间": 卡片.创建时间,
        "更新时间": 卡片.更新时间,
        "完成时间": 卡片.完成时间,
        "元数据": 卡片.元数据,
    }
