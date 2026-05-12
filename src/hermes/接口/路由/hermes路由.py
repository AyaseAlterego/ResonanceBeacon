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


def _构建系统上下文() -> str:
    流水线列表 = 存储实例.获取所有流水线()
    智能体列表 = 存储实例.获取所有智能体()
    待审批列表 = 存储实例.获取待审批()

    context = "你是 Hermes，起源信标系统的元智能体。回答要简洁，关键信息用 **加粗** 标注。\n\n当前系统状态:\n"
    if 流水线列表:
        运行中 = sum(1 for p in 流水线列表 if p.状态 == "running")
        已完成 = sum(1 for p in 流水线列表 if p.状态 == "completed")
        context += f"- 流水线: {len(流水线列表)} 条 (运行中 {运行中}, 已完成 {已完成})\n"
        for p in 流水线列表[:5]:
            context += f"  · {p.名称}: {p.状态}\n"
    if 智能体列表:
        context += f"- 智能体: {len(智能体列表)} 个\n"
        for a in 智能体列表[:5]:
            status = "在线" if a.是否在线 else "离线"
            context += f"  · {a.名称}: {status}\n"
    if 待审批列表:
        context += f"- 待审批: {len(待审批列表)} 项\n"
    return context


@router.post("/chat", response_model=对话响应)
async def hermes_对话(请求: 对话请求):
    try:
        claude = 存储实例.查找智能体("claude_code")
        if claude and claude.是否在线:
            try:
                import subprocess, json
                prompt = _构建系统上下文() + f"\n用户问题: {请求.message}"
                result = subprocess.run(
                    ["claude", "-p", prompt],
                    capture_output=True, text=True, timeout=120,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return 对话响应(reply=result.stdout.strip()[:1000])
            except Exception as e:
                logger.warning(f"Claude Code 调用失败，回退到本地回复: {e}")

        # 本地回退
        if not 存储实例.获取所有流水线() and not 存储实例.获取所有智能体():
            return 对话响应(reply="我是 Hermes。目前系统还没有数据，创建流水线后我可以为你提供进度信息。")

        reply = f"收到消息：「{请求.message}」。\n"
        流水线列表 = 存储实例.获取所有流水线()
        if 流水线列表:
            运行中 = sum(1 for p in 流水线列表 if p.状态 == "running")
            已完成 = sum(1 for p in 流水线列表 if p.状态 == "completed")
            reply += f"\n· 流水线: {len(流水线列表)} 条 (运行中 {运行中} / 已完成 {已完成})"
        if 存储实例.获取所有智能体():
            reply += f"\n· 智能体: {len(存储实例.获取所有智能体())} 个"
        if 存储实例.获取待审批():
            reply += f"\n· 待审批: {len(存储实例.获取待审批())} 项"
        reply += "\n\n我可以回答项目进度相关的问题。"
        return 对话响应(reply=reply)
    except Exception as e:
        logger.error(f"Hermes 对话出错: {e}")
        return 对话响应(reply="我遇到了一些技术问题，请稍后再试。")
