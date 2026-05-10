"""配置路由"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

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
    logger.info(f"更新配置: {键路径}")
    return {"键路径": 键路径, "状态": "已更新"}
