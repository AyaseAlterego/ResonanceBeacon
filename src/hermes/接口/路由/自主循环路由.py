"""自主循环路由

提供自主循环引擎的状态查询和控制 API。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/自主循环", tags=["自主循环"])

# 全局自主循环引擎实例（由应用初始化时注入）
自主循环引擎实例 = None


def 设置自主循环引擎实例(实例):
    """设置自主循环引擎实例"""
    global 自主循环引擎实例
    自主循环引擎实例 = 实例


class 启动请求(BaseModel):
    扫描间隔秒: Optional[int] = None


class 审批响应请求(BaseModel):
    响应: str  # "YES" or "NO"
    反馈: str = ""


@router.get("/状态")
async def 获取自主循环状态():
    """获取自主循环引擎状态"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

    return 自主循环引擎实例.获取状态()


@router.post("/启动")
async def 启动自主循环(请求: 启动请求 = None):
    """启动自主循环"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

    if 请求 and 请求.扫描间隔秒:
        自主循环引擎实例.配置.扫描间隔秒 = 请求.扫描间隔秒

    import asyncio
    asyncio.create_task(自主循环引擎实例.启动())

    return {"成功": True, "消息": "自主循环已启动"}


@router.post("/停止")
async def 停止自主循环():
    """停止自主循环"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

    import asyncio
    asyncio.create_task(自主循环引擎实例.停止())

    return {"成功": True, "消息": "自主循环已停止"}


@router.post("/暂停")
async def 暂停自主循环():
    """暂停自主循环"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

    自主循环引擎实例.暂停()
    return {"成功": True, "消息": "自主循环已暂停"}


@router.post("/恢复")
async def 恢复自主循环():
    """恢复自主循环"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

    自主循环引擎实例.恢复()
    return {"成功": True, "消息": "自主循环已恢复"}


@router.get("/事件日志")
async def 获取事件日志(限制: int = 50):
    """获取自主循环事件日志"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

    日志 = 自主循环引擎实例.获取事件日志(限制)

    return {
        "事件列表": [
            {
                "ID": e.ID,
                "类型": e.类型,
                "描述": e.描述,
                "时间": e.时间,
                "元数据": e.元数据,
            }
            for e in 日志
        ],
        "总数": len(日志),
    }


@router.post("/审批/{卡片ID}")
async def 提交审批响应(卡片ID: str, 请求: 审批响应请求):
    """提交 YES/NO 审批响应"""
    if not 自主循环引擎实例:
        raise HTTPException(status_code=503, detail="自主循环引擎未初始化")

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
