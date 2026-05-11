"""Hermes 对话路由"""
from fastapi import APIRouter
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class 对话请求(BaseModel):
    """Hermes 对话请求"""
    message: str


class 对话响应(BaseModel):
    """Hermes 对话响应"""
    reply: str


@router.post("/chat", response_model=对话响应)
async def hermes_对话(请求: 对话请求):
    """处理 Hermes 对话消息"""
    try:
        reply = (
            f"我是 Hermes，已收到你的消息：「{请求.message}」。"
            f"项目「起源信标」正在稳定运行中，当前版本 0.1.0，"
            f"所有智能体状态正常。有什么我可以进一步协助你的吗？"
        )
        return 对话响应(reply=reply)
    except Exception as e:
        logger.error(f"Hermes 对话出错: {e}")
        return 对话响应(reply="我遇到了一些技术问题，请稍后再试。")
