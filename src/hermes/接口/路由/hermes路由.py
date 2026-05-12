"""Hermes 对话路由"""
from fastapi import APIRouter
from pydantic import BaseModel
import logging

from ..存储 import 存储实例

logger = logging.getLogger(__name__)
router = APIRouter()


class 对话请求(BaseModel):
    message: str


class 对话响应(BaseModel):
    reply: str


@router.post("/chat", response_model=对话响应)
async def hermes_对话(请求: 对话请求):
    try:
        流水线列表 = 存储实例.获取所有流水线()
        智能体列表 = 存储实例.获取所有智能体()
        待审批列表 = 存储实例.获取待审批()

        运行中 = sum(1 for p in 流水线列表 if p.状态 == "running")
        已完成 = sum(1 for p in 流水线列表 if p.状态 == "completed")
        在线智能体 = sum(1 for a in 智能体列表 if a.是否在线)

        reply = (
            f"我是 Hermes，收到你的消息：「{请求.message}」。\n\n"
            f"📊 **当前状态**\n"
            f"· 流水线: {len(流水线列表)} 条 (运行中 {运行中} / 已完成 {已完成})\n"
            f"· 智能体: {len(智能体列表)} 个 ({在线智能体} 在线)\n"
            f"· 待审批: {len(待审批列表)} 项\n\n"
            f"我是你的元智能体助手，随时可以问我项目进度、风险信息或帮我执行操作。"
        )
        return 对话响应(reply=reply)
    except Exception as e:
        logger.error(f"Hermes 对话出错: {e}")
        return 对话响应(reply="我遇到了一些技术问题，请稍后再试。")
