"""项目对话路由"""
import re
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..存储 import 存储实例

logger = logging.getLogger(__name__)
router = APIRouter()


class 发送消息请求(BaseModel):
    内容: str


阶段技能映射 = {
    "需求分析": "brainstorming",
    "架构设计": "writing-plans",
    "方案确认": "human-gate",
    "开发执行": "subagent-driven-development",
    "代码审查": "requesting-code-review",
    "完成": "finishing-a-development-branch",
}

制品标记模式 = {
    "需求分析": (r"\[SUBMIT_SPEC\](.*?)\[/SUBMIT_SPEC\]", "spec", "设计文档", "brainstorming"),
    "架构设计": (r"\[SUBMIT_PLAN\](.*?)\[/SUBMIT_PLAN\]", "plan", "实施计划", "writing-plans"),
}


def _构建阶段prompt(项目, 对话消息列表, 制品列表):
    阶段 = 项目.阶段
    已有制品上下文 = ""
    for 制品 in 制品列表:
        已有制品上下文 += f"\n--- {制品.名称} (已确认) ---\n{制品.内容}\n"

    历史上下文 = ""
    for 消息 in 对话消息列表[-20:]:
        if 消息.角色 == "user":
            历史上下文 += f"用户: {消息.内容}\n"
        elif 消息.角色 == "hermes":
            历史上下文 += f"Hermes: {消息.内容}\n"
        elif 消息.角色 == "system":
            历史上下文 += f"[系统] {消息.内容}\n"

    prompts = {
        "需求分析": f"""你是 Hermes，起源信标系统的元智能体。当前项目「{项目.名称}」处于「需求分析」阶段。

你必须遵循 brainstorming 技能：

## 流程
1. 探索项目上下文 — 了解现有代码、文档、最近提交
2. 一次问一个澄清问题 — 理解目的、约束、成功标准
3. 提出2-3种方案 — 附带权衡和你的推荐
4. 分段呈现设计 — 每段确认后再继续
5. 输出设计文档 — 用 [SUBMIT_SPEC]...[/SUBMIT_SPEC] 包裹完整的设计文档

## 硬约束
- 在呈现设计并获得用户批准之前，不进入任何实现
- 每个项目都走这个流程，不论看起来多简单
- YAGNI：从所有设计中移除不必要的功能
- 一次只问一个问题

项目信息：{项目.名称} - {项目.描述}
{已有制品上下文}
对话历史：
{历史上下文}""",

        "架构设计": f"""你是 Hermes，起源信标系统的元智能体。当前项目「{项目.名称}」处于「架构设计」阶段。

设计文档已经确认，你必须遵循 writing-plans 技能：

## 流程
1. 映射文件结构 — 哪些文件需要创建或修改，每个文件负责什么
2. 分解为2-5分钟的 bite-sized 任务
3. 每个任务包含：精确文件路径、完整代码、验证步骤
4. 强制 TDD：先写失败测试 → 验证失败 → 写最小实现 → 验证通过
5. 输出实施计划 — 用 [SUBMIT_PLAN]...[/SUBMIT_PLAN] 包裹

## 硬约束
- 不允许占位符：每个步骤必须包含实际内容
- DRY, YAGNI, TDD, 频繁提交
- 精确文件路径，完整代码，精确命令

{已有制品上下文}
对话历史：
{历史上下文}""",

        "方案确认": f"""你是 Hermes，起源信标系统的元智能体。当前项目「{项目.名称}」处于「方案确认」阶段。

你需要汇总所有制品，向用户展示完整方案，等待用户确认或提出修改意见。

## 展示内容
1. 设计文档（spec）— brainstorming 产出
2. 实施计划（plan）— writing-plans 产出
3. 文件结构映射
4. 预估任务数

确认后将自动进入开发阶段，OpenCode 智能体将按计划执行。

{已有制品上下文}
对话历史：
{历史上下文}""",

        "开发执行": f"""你是 Hermes，起源信标系统的元智能体。当前项目「{项目.名称}」处于「开发执行」阶段。

OpenCode 智能体正在按照实施计划执行开发。你不需要编写代码。

你的任务是监控和协调：
1. 汇报开发进度
2. 转达智能体遇到的问题给用户决策
3. 开发完成后通知用户进入代码审查阶段

{已有制品上下文}
对话历史：
{历史上下文}""",

        "代码审查": f"""你是 Hermes，起源信标系统的元智能体。当前项目「{项目.名称}」处于「代码审查」阶段。

代码审查正在进行中。你的任务是：
1. 汇报审查结果
2. 如果有需要修改的地方，协调修复
3. 审查通过后进入完成阶段

{已有制品上下文}
对话历史：
{历史上下文}""",

        "完成": f"""你是 Hermes，起源信标系统的元智能体。项目「{项目.名称}」已完成开发。

你可以回答用户关于项目的问题，或帮助用户开始新的项目。

{已有制品上下文}""",
    }

    return prompts.get(阶段, prompts["需求分析"])


def _调用AI(prompt_text: str) -> str | None:
    import os
    from .hermes路由 import _读取Hermes配置

    hcfg = _读取Hermes配置()
    if hcfg:
        try:
            import httpx
            resp = httpx.post(
                f"{hcfg['base_url']}/chat/completions",
                headers={"Authorization": f"Bearer {hcfg['api_key']}", "Content-Type": "application/json"},
                json={"model": hcfg["model"], "messages": [
                    {"role": "system", "content": "你是 Hermes，起源信标系统的元智能体。"},
                    {"role": "user", "content": prompt_text},
                ], "max_tokens": 2000},
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("choices"):
                    return data["choices"][0]["message"]["content"].strip()[:3000]
        except Exception as e:
            logger.warning(f"Hermes AI 失败: {e}")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt_text}],
            )
            if msg.content and msg.content[0].text:
                return msg.content[0].text.strip()[:3000]
        except Exception as e:
            logger.warning(f"Anthropic 失败: {e}")

    import shutil, subprocess
    cc = shutil.which("claude")
    if cc:
        try:
            r = subprocess.run([cc, "-p", prompt_text], capture_output=True, text=True, timeout=120)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()[:3000]
        except Exception as e:
            logger.warning(f"Claude 失败: {e}")

    return None


def _解析制品(阶段: str, 回复内容: str) -> dict | None:
    标记信息 = 制品标记模式.get(阶段)
    if not 标记信息:
        return None
    模式, 制品类型, 名称, 技能 = 标记信息
    匹配 = re.search(模式, 回复内容, re.DOTALL)
    if not 匹配:
        return None
    制品内容 = 匹配.group(1).strip()
    if len(制品内容) < 50:
        return None
    return {"制品类型": 制品类型, "名称": 名称, "内容": 制品内容, "技能": 技能}


def _获取技能状态(阶段: str, 阶段产出):
    技能 = 阶段技能映射.get(阶段, "unknown")
    return {
        "当前技能": 技能,
        "技能阶段": "design_approved" if 阶段产出 else "in_progress",
        "可推进": 阶段产出 is not None,
    }


@router.get("/{项目ID}/对话/")
async def 获取对话(项目ID: str):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    对话 = 存储实例.获取项目对话(项目ID)
    if not 对话:
        raise HTTPException(status_code=404, detail="对话不存在")
    消息列表 = 存储实例.获取对话消息(对话.ID)
    return {
        "对话ID": 对话.ID,
        "项目ID": 对话.项目ID,
        "消息列表": [
            {
                "ID": m.ID,
                "对话ID": m.对话ID,
                "角色": m.角色,
                "内容": m.内容,
                "元数据": m.元数据,
                "创建时间": m.创建时间,
            }
            for m in 消息列表
        ],
    }


@router.post("/{项目ID}/对话/消息")
async def 发送消息(项目ID: str, 请求: 发送消息请求):
    项目 = 存储实例.获取项目(项目ID)
    if not 项目:
        raise HTTPException(status_code=404, detail="项目不存在")
    对话 = 存储实例.获取项目对话(项目ID)
    if not 对话:
        raise HTTPException(status_code=404, detail="对话不存在")

    用户消息 = 存储实例.添加消息(对话.ID, "user", 请求.内容)

    对话消息列表 = 存储实例.获取对话消息(对话.ID)
    制品列表 = 存储实例.获取项目制品(项目ID)

    prompt = _构建阶段prompt(项目, 对话消息列表[:-1], 制品列表)
    prompt += f"\n用户最新消息: {请求.内容}"

    回复文本 = _调用AI(prompt)

    if not 回复文本:
        回复文本 = "抱歉，我暂时无法连接 AI 后端。请确保已配置 ANTHROPIC_API_KEY 或安装了 Claude Code CLI。"

    制品解析结果 = _解析制品(项目.阶段, 回复文本)

    阶段产出 = None
    if 制品解析结果:
        制品 = 存储实例.创建制品(
            项目ID=项目ID,
            制品类型=制品解析结果["制品类型"],
            名称=制品解析结果["名称"],
            内容=制品解析结果["内容"],
            阶段=项目.阶段,
            技能=制品解析结果["技能"],
        )
        阶段产出 = {
            "制品ID": 制品.ID,
            "制品类型": 制品.制品类型,
            "名称": 制品.名称,
            "内容": 制品.内容,
            "阶段": 制品.阶段,
            "技能": 制品.技能,
        }

    hermes消息 = 存储实例.添加消息(对话.ID, "hermes", 回复文本, {
        "阶段": 项目.阶段,
        "技能": 阶段技能映射.get(项目.阶段, "unknown"),
        "制品ID": 阶段产出["制品ID"] if 阶段产出 else None,
    })

    return {
        "用户消息": {
            "ID": 用户消息.ID,
            "对话ID": 用户消息.对话ID,
            "角色": 用户消息.角色,
            "内容": 用户消息.内容,
            "创建时间": 用户消息.创建时间,
        },
        "Hermes回复": {
            "ID": hermes消息.ID,
            "对话ID": hermes消息.对话ID,
            "角色": hermes消息.角色,
            "内容": hermes消息.内容,
            "创建时间": hermes消息.创建时间,
        },
        "项目阶段": 项目.阶段,
        "阶段产出": 阶段产出,
        "技能状态": _获取技能状态(项目.阶段, 阶段产出),
    }
