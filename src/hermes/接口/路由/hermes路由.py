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

        if not 流水线列表 and not 智能体列表 and not 待审批列表:
            return 对话响应(reply=f"我是 Hermes。目前系统还没有数据，创建流水线后我可以为你提供进度信息。")

        运行中 = sum(1 for p in 流水线列表 if p.状态 == "running")
        已完成 = sum(1 for p in 流水线列表 if p.状态 == "completed")

        reply = f"收到消息：「{请求.message}」。\n"
        if 流水线列表:
            reply += f"\n· 流水线: {len(流水线列表)} 条 (运行中 {运行中} / 已完成 {已完成})"
        if 智能体列表:
            reply += f"\n· 智能体: {len(智能体列表)} 个"
        if 待审批列表:
            reply += f"\n· 待审批: {len(待审批列表)} 项"
        reply += "\n\n我可以回答项目进度相关的问题。"
        return 对话响应(reply=reply)
    except Exception as e:
        logger.error(f"Hermes 对话出错: {e}")
        return 对话响应(reply="我遇到了一些技术问题，请稍后再试。")
