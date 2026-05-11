"""插件市场路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from pathlib import Path
import logging

from src.hermes.插件.系统 import 插件管理器, 插件类型
from src.hermes.插件.市场 import 插件市场, 市场插件信息, 已安装插件信息, 插件状态

logger = logging.getLogger(__name__)
router = APIRouter()

_插件管理器实例 = 插件管理器(插件路径="./插件")
_插件市场实例 = 插件市场(_插件管理器实例)

class 搜索请求(BaseModel):
    关键词: str = ""
    类型: str | None = None
    标签: str = ""

class 插件信息响应(BaseModel):
    ID: str
    名称: str
    版本: str
    类型: str
    描述: str = ""
    作者: str = ""
    标签: list[str] = []
    下载次数: int = 0
    评分: float = 0.0

class 已安装插件响应(BaseModel):
    ID: str
    名称: str
    已安装版本: str
    最新版本: str
    状态: str
    安装路径: str = ""

class 操作结果响应(BaseModel):
    成功: bool
    消息: str

class 插件详情响应(BaseModel):
    ID: str
    名称: str
    版本: str
    类型: str
    描述: str = ""
    作者: str = ""
    依赖项: list[str] = []
    标签: list[str] = []
    下载次数: int = 0
    评分: float = 0.0
    下载地址: str = ""
    源码地址: str = ""

def _市场插件转响应(信息: 市场插件信息) -> 插件信息响应:
    类型值 = 信息.类型.value if isinstance(信息.类型, 插件类型) else 信息.类型
    return 插件信息响应(
        ID=信息.ID,
        名称=信息.名称,
        版本=信息.版本,
        类型=类型值,
        描述=信息.描述,
        作者=信息.作者,
        标签=信息.标签,
        下载次数=信息.下载次数,
        评分=信息.评分,
    )

def _已安装插件转响应(信息: 已安装插件信息) -> 已安装插件响应:
    return 已安装插件响应(
        ID=信息.ID,
        名称=信息.名称,
        已安装版本=信息.已安装版本,
        最新版本=信息.最新版本,
        状态=信息.状态.value if isinstance(信息.状态, 插件状态) else 信息.状态,
        安装路径=信息.安装路径,
    )

@router.get("/搜索")
async def 搜索插件(关键词: str = "", 类型: str | None = None, 标签: str = ""):
    插件类型枚举 = None
    if 类型:
        try:
            插件类型枚举 = 插件类型(类型)
        except ValueError:
            pass
    结果 = await _插件市场实例.搜索插件(关键词=关键词, 类型=插件类型枚举, 标签=标签)
    return {"插件列表": [_市场插件转响应(信息) for 信息 in 结果], "总数": len(结果)}

@router.get("/列表")
async def 获取可用插件列表():
    结果 = await _插件市场实例.获取可用插件列表()
    return {"插件列表": [_市场插件转响应(信息) for 信息 in 结果], "总数": len(结果)}

@router.get("/已安装")
async def 获取已安装插件():
    结果 = await _插件市场实例.获取已安装插件()
    return {"插件列表": [_已安装插件转响应(信息) for 信息 in 结果], "总数": len(结果)}

@router.post("/安装/{插件ID}", response_model=操作结果响应)
async def 安装插件(插件ID: str):
    结果 = await _插件市场实例.安装插件(插件ID)
    return 操作结果响应(成功=结果["成功"], 消息=结果["消息"])

@router.post("/卸载/{插件ID}", response_model=操作结果响应)
async def 卸载插件(插件ID: str):
    结果 = await _插件市场实例.卸载插件(插件ID)
    return 操作结果响应(成功=结果["成功"], 消息=结果["消息"])

@router.post("/更新/{插件ID}", response_model=操作结果响应)
async def 更新插件(插件ID: str):
    结果 = await _插件市场实例.更新插件(插件ID)
    return 操作结果响应(成功=结果["成功"], 消息=结果["消息"])

@router.get("/详情/{插件ID}", response_model=插件详情响应)
async def 获取插件详情(插件ID: str):
    详情 = await _插件市场实例.获取插件详情(插件ID)
    if not 详情:
        raise HTTPException(status_code=404, detail=f"插件未找到: {插件ID}")
    类型值 = 详情.类型.value if isinstance(详情.类型, 插件类型) else 详情.类型
    return 插件详情响应(
        ID=详情.ID,
        名称=详情.名称,
        版本=详情.版本,
        类型=类型值,
        描述=详情.描述,
        作者=详情.作者,
        依赖项=详情.依赖项,
        标签=详情.标签,
        下载次数=详情.下载次数,
        评分=详情.评分,
        下载地址=详情.下载地址,
        源码地址=详情.源码地址,
    )
