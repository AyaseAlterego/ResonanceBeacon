"""配置路由"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any
from pathlib import Path
import json5
import logging

from ...配置.合并 import 安全深度合并
from ...配置.配置加载器 import 获取配置, 配置加载器实例

logger = logging.getLogger(__name__)
router = APIRouter()

DANGEROUS_KEYS = frozenset(["__proto__", "constructor", "prototype"])

class 配置响应(BaseModel):
    """配置响应"""
    配置: dict[str, Any]
    来源: str

@router.get("/")
async def 获取配置():
    """获取当前配置"""
    return 配置响应(
        配置={
            "智能体": {
                "claude_code": {"模型": "claude-sonnet-4-20250514"},
                "opencode": {"模型": "default"},
                "codex": {"模型": "default"}
            },
            "流水线": {
                "默认超时": 600,
                "最大重试次数": 3
            },
            "后台任务": {
                "每智能体最大并发": 5,
                "熔断器阈值": 5
            }
        },
        来源="默认值"
    )

@router.get("/合并后")
async def 获取合并后配置():
    """获取合并后的完整配置"""
    return 配置响应(
        配置={
            "智能体": {},
            "流水线": {},
            "后台任务": {}
        },
        来源="合并后"
    )

@router.put("/{键路径}")
async def 更新配置(键路径: str, 值: Any):
    """更新配置"""
    路径部分 = 键路径.replace("/", ".").split(".")

    for 部分 in 路径部分:
        if 部分 in DANGEROUS_KEYS:
            return JSONResponse(
                status_code=400,
                content={"错误": f"键路径包含危险键: {部分}"}
            )

    更新字典 = 值
    for 部分 in reversed(路径部分):
        更新字典 = {部分: 更新字典}

    try:
        当前配置实例 = 获取配置()
        当前配置字典 = 当前配置实例.model_dump()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"错误": f"获取当前配置失败: {str(e)}"}
        )

    try:
        合并后字典 = 安全深度合并(当前配置字典, 更新字典)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"错误": str(e)}
        )

    try:
        项目路径 = Path.cwd()
        配置目录 = 项目路径 / ".hermes"
        配置目录.mkdir(parents=True, exist_ok=True)
        配置文件路径 = 配置目录 / "配置.jsonc"
        配置文件路径.write_text(
            json5.dumps(合并后字典, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"错误": f"写入配置文件失败: {str(e)}"}
        )

    配置加载器实例.清除缓存()

    return {"键路径": 键路径, "状态": "已更新"}
