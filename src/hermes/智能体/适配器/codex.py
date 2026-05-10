"""Codex适配器实现"""
import time
import asyncio
from typing import AsyncIterator, Any, Optional
import logging

from ..基础 import (
    智能体适配器,
    智能体能力,
    智能体类别,
    智能体成本,
    任务结果,
    上下文包
)

logger = logging.getLogger(__name__)

class Codex适配器(智能体适配器):
    """
    Codex适配器

    通过Codex CLI或API执行任务
    专注于代码生成和补全
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._客户端 = None

    @property
    def 智能体ID(self) -> str:
        return "codex"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "java", "csharp"],
                上下文窗口=16000,
                每千令牌成本=0.0004,
                最大并发任务数=10
            ),
            智能体能力(
                名称="test_generation",
                语言列表=["python", "javascript", "typescript"],
                上下文窗口=16000,
                每千令牌成本=0.0004,
                最大并发任务数=10
            ),
            智能体能力(
                名称="code_explanation",
                语言列表=["python", "javascript", "typescript", "java"],
                上下文窗口=16000,
                每千令牌成本=0.0004,
                最大并发任务数=10
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.专家

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.便宜

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化Codex客户端"""
        self._配置.update(配置)
        try:
            import openai
            self._客户端 = openai.AsyncOpenAI(
                api_key=配置.get("api_key"),
                base_url=配置.get("base_url")
            )
            logger.info(f"Codex适配器初始化成功 (模型: {self._模型})")
        except ImportError:
            logger.warning("未安装openai库，Codex适配器将以模拟模式运行")

    async def 健康检查(self) -> bool:
        """检查Codex是否可用"""
        if not self._客户端:
            return False
        try:
            响应 = await self._客户端.chat.completions.create(
                model=self._模型,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"Codex健康检查失败: {e}")
            return False

    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        """执行单个任务"""
        开始时间 = time.time()

        try:
            提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

            if not self._客户端:
                raise RuntimeError("Codex客户端未初始化")

            响应 = await self._客户端.chat.completions.create(
                model=self._模型,
                messages=[{"role": "user", "content": 提示词}],
                max_tokens=self._配置.get("max_tokens", 4096),
                temperature=self._配置.get("temperature", 0.7)
            )

            输出文本 = 响应.choices[0].message.content or ""
            使用的令牌数 = (响应.usage.prompt_tokens or 0) + (响应.usage.completion_tokens or 0)
            成本 = self._计算成本(响应.usage)

            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)

            制品 = self._提取制品(输出文本, 任务类型)

            return 任务结果(
                任务ID=任务ID,
                状态="completed",
                输出数据={
                    "文本": 输出文本,
                    "任务类型": 任务类型,
                    "模型": self._模型
                },
                制品列表=制品,
                使用的令牌数=使用的令牌数,
                成本=成本,
                耗时毫秒=耗时毫秒,
                错误=None
            )

        except Exception as e:
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)
            logger.error(f"任务 {任务ID} 执行失败: {e}", exc_info=True)
            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时毫秒,
                错误=str(e)
            )

    async def 流式执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行任务"""
        提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

        if not self._客户端:
            raise RuntimeError("Codex客户端未初始化")

        响应 = await self._客户端.chat.completions.create(
            model=self._模型,
            messages=[{"role": "user", "content": 提示词}],
            max_tokens=self._配置.get("max_tokens", 4096),
            stream=True
        )

        async for 块 in 响应:
            if 块.choices[0].delta.content:
                yield {"type": "text", "text": 块.choices[0].delta.content}

        yield {"type": "done", "任务ID": 任务ID}

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        logger.warning(f"Codex适配器不支持取消任务 {任务ID}")
        return False

    def _构建提示词(self, 任务类型: str, 输入数据: dict[str, Any], 上下文: 上下文包) -> str:
        """构建提示词"""
        from ..提示词模板 import 提示词模板管理器

        模板管理器 = 提示词模板管理器()

        # 获取模板名称
        模板名称 = 模板管理器.根据任务类型获取模板(任务类型)

        # 构建上下文
        上下文数据 = {
            "需求描述": 输入数据.get("需求", 输入数据.get("description", "")),
            "代码内容": 输入数据.get("代码", 输入数据.get("code", "")),
            "代码语言": 输入数据.get("语言", 输入数据.get("language", "python")),
            "测试框架": 输入数据.get("测试框架", "pytest"),
        }

        # 生成提示词
        提示词结果 = 模板管理器.生成提示词(模板名称, 上下文数据)

        if 提示词结果:
            return 提示词结果["用户提示词"]
        else:
            # 如果模板生成失败，使用默认提示词
            部分 = ["你是一个专业的代码生成助手。"]

            if 任务类型 == "code_generation":
                部分.append("请根据需求生成高质量的代码。")
            elif 任务类型 == "test_generation":
                部分.append("请为给定代码生成全面的测试用例。")
            elif 任务类型 == "code_explanation":
                部分.append("请详细解释代码的功能和逻辑。")

            if 输入数据:
                部分.append("\n## 输入数据\n")
                for 键, 值 in 输入数据.items():
                    部分.append(f"**{键}**: {值}")

            return "\n".join(部分)

    def _计算成本(self, 使用量) -> float:
        """计算API调用成本"""
        输入成本 = (使用量.prompt_tokens or 0) * 0.0004 / 1000
        输出成本 = (使用量.completion_tokens or 0) * 0.0004 / 1000
        return 输入成本 + 输出成本

    def _提取制品(self, 输出文本: str, 任务类型: str) -> list[dict]:
        """从输出中提取制品"""
        制品 = []
        if "```" in 输出文本:
            代码块 = []
            在代码块中 = False

            for 行 in 输出文本.split("\n"):
                if 行.startswith("```"):
                    在代码块中 = not 在代码块中
                    if not 在代码块中 and 代码块:
                        制品.append({
                            "类型": "code",
                            "内容": "\n".join(代码块),
                            "语言": "unknown"
                        })
                        代码块 = []
                elif 在代码块中:
                    代码块.append(行)

        return 制品
