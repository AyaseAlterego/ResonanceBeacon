"""项目路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..存储 import 存储实例

router = APIRouter()


class 创建项目请求(BaseModel):
    名称: str
    描述: str = ""


class 更新阶段请求(BaseModel):
    阶段: str


class 确认请求(BaseModel):
    反馈: str = ""


class 拒绝请求(BaseModel):
    反馈: str = ""


阶段转换表 = {
    "需求分析": "架构设计",
    "架构设计": "方案确认",
    "方案确认": "开发执行",
    "开发执行": "代码审查",
    "代码审查": "完成",
}


@router.get("/")
async def 列出项目():
    项目列表 = 存储实例.获取所有项目()
    return {
        "项目列表": [
            {
                "ID": p.ID,
                "名称": p.名称,
                "描述": p.描述,
                "阶段": p.阶段,
                "工作目录": p.工作目录,
                "创建时间": p.创建时间,
                "更新时间": p.更新时间,
            }
            for p in 项目列表
        ],
        "总数": len(项目列表),
    }


@router.post("/")
async def 创建项目(请求: 创建项目请求):
    if not 请求.名称.strip():
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    项目 = 存储实例.创建项目(名称=请求.名称, 描述=请求.描述)
    return {
        "ID": 项目.ID,
        "名称": 项目.名称,
        "描述": 项目.描述,
        "阶段": 项目.阶段,
        "工作目录": 项目.工作目录,
        "创建时间": 项目.创建时间,
        "更新时间": 项目.更新时间,
    }


@router.get("/{项目ID}")
async def 获取项目(项目ID: str):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    制品列表 = 存储实例.获取项目制品(项目ID)
    return {
        "ID": 项目.ID,
        "名称": 项目.名称,
        "描述": 项目.描述,
        "阶段": 项目.阶段,
        "工作目录": 项目.工作目录,
        "创建时间": 项目.创建时间,
        "更新时间": 项目.更新时间,
        "制品列表": [
            {
                "ID": a.ID,
                "制品类型": a.制品类型,
                "名称": a.名称,
                "阶段": a.阶段,
                "技能": a.技能,
                "创建时间": a.创建时间,
            }
            for a in 制品列表
        ],
    }


@router.put("/{项目ID}/阶段")
async def 更新阶段(项目ID: str, 请求: 更新阶段请求):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    项目 = 存储实例.更新项目阶段(项目ID, 请求.阶段)
    return {
        "ID": 项目.ID,
        "名称": 项目.名称,
        "阶段": 项目.阶段,
    }


@router.post("/{项目ID}/确认")
async def 确认阶段(项目ID: str, 请求: 确认请求):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    原阶段 = 项目.阶段
    新阶段 = 阶段转换表.get(原阶段)
    if not 新阶段:
        raise HTTPException(status_code=400, detail=f"阶段 {原阶段} 无法推进")
    存储实例.更新项目阶段(项目ID, 新阶段)
    存储实例.添加消息(
        存储实例.获取项目对话(项目ID).ID,
        "system",
        f"用户确认了 {原阶段} 阶段，进入 {新阶段} 阶段。{请求.反馈}",
    )
    return {
        "项目ID": 项目ID,
        "原阶段": 原阶段,
        "新阶段": 新阶段,
    }


@router.post("/{项目ID}/拒绝")
async def 拒绝阶段(项目ID: str, 请求: 拒绝请求):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    对话 = 存储实例.获取项目对话(项目ID)
    if 对话:
        存储实例.添加消息(
            对话.ID,
            "system",
            f"用户拒绝了当前阶段产出：{请求.反馈}。请根据反馈继续修改。",
        )
    return {
        "项目ID": 项目ID,
        "阶段": 项目.阶段,
        "消息": "已拒绝，回到对话继续讨论",
    }
