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


def _读取Hermes配置() -> dict | None:
    import os, yaml
    配置路径 = os.path.join(os.path.expanduser("~"), ".hermes", "config.yaml")
    if not os.path.exists(配置路径):
        return None
    with open(配置路径, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg:
        return None
    providers = cfg.get("custom_providers", [])
    for p in providers:
        if p.get("name") == "opencode":
            return {"base_url": p["base_url"], "api_key": p["api_key"], "model": p["model"]}
    return None


def _调用AI(用户消息: str) -> str | None:
    prompt_text = _构建系统上下文() + f"\n用户问题: {用户消息}"
    import os, json, subprocess, shutil, httpx

    # 1. Hermes 配置的 AI API（优先）
    hcfg = _读取Hermes配置()
    if hcfg:
        try:
            resp = httpx.post(
                f"{hcfg['base_url']}/chat/completions",
                headers={"Authorization": f"Bearer {hcfg['api_key']}",
                         "Content-Type": "application/json"},
                json={"model": hcfg["model"], "messages": [
                    {"role": "system", "content": "你是 Hermes，起源信标系统的元智能体。回答简洁有用。"},
                    {"role": "user", "content": prompt_text}],
                    "max_tokens": 1000},
                timeout=120
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("choices"):
                    return data["choices"][0]["message"]["content"].strip()[:1200]
        except Exception as e:
            logger.warning(f"Hermes AI 失败: {e}")

    # 2. Anthropic API
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), max_tokens=1024,
                messages=[{"role": "user", "content": prompt_text}])
            if msg.content and msg.content[0].text:
                return msg.content[0].text.strip()[:1000]
        except Exception as e:
            logger.warning(f"Anthropic 失败: {e}")

    # 3. Claude CLI
    cc = shutil.which("claude")
    if cc:
        try:
            r = subprocess.run([cc, "-p", prompt_text], capture_output=True, text=True, timeout=120)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()[:1000]
        except Exception as e:
            logger.warning(f"Claude 失败: {e}")

    return None


@router.post("/chat", response_model=对话响应)
async def hermes_对话(请求: 对话请求):
    try:
        reply = _调用AI(请求.message)
        if reply:
            return 对话响应(reply=reply)
        智能体列表 = 存储实例.获取所有智能体()
        return 对话响应(reply=(
            "未检测到可用的 AI 后端。\n\n"
            "如需智能回复，请任选其一：\n"
            "1. 设置 ANTHROPIC_API_KEY 环境变量\n"
            "2. 安装 Claude Code CLI: npm i -g @anthropic-ai/claude-code\n\n"
            f"当前系统状态: 智能体 {len(智能体列表)} 个，流水线 {len(存储实例.获取所有流水线())} 条。"
        ))
    except Exception as e:
        logger.error(f"Hermes: {e}")
        return 对话响应(reply=f"出错: {e}")
