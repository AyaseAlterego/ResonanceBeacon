"""制品路由"""
from fastapi import APIRouter, HTTPException
from ..存储 import 存储实例

router = APIRouter()


@router.get("/{项目ID}/制品/")
async def 列出制品(项目ID: str):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    制品列表 = 存储实例.获取项目制品(项目ID)
    return {
        "制品列表": [
            {
                "ID": a.ID,
                "项目ID": a.项目ID,
                "制品类型": a.制品类型,
                "名称": a.名称,
                "内容": a.内容,
                "阶段": a.阶段,
                "技能": a.技能,
                "文件路径": a.文件路径,
                "创建时间": a.创建时间,
            }
            for a in 制品列表
        ],
        "总数": len(制品列表),
    }


@router.get("/{项目ID}/制品/{制品ID}")
async def 获取制品(项目ID: str, 制品ID: str):
    制品 = 存储实例.制品列表.get(制品ID)
    if not 制品 or 制品.项目ID != 项目ID:
        raise HTTPException(status_code=404, detail="制品不存在")
    return {
        "ID": 制品.ID,
        "项目ID": 制品.项目ID,
        "制品类型": 制品.制品类型,
        "名称": 制品.名称,
        "内容": 制品.内容,
        "阶段": 制品.阶段,
        "技能": 制品.技能,
        "文件路径": 制品.文件路径,
        "创建时间": 制品.创建时间,
    }
