"""OpenCode适配器实现"""
import time
import asyncio
from typing import AsyncIterator, Any, Optional
import logging
import json

from ..基础 import (
    智能体适配器,
    智能体能力,
    智能体类别,
    智能体成本,
    任务结果,
    上下文包
)

logger = logging.getLogger(__name__)

class OpenCode适配器(智能体适配器):
    """
    OpenCode适配器

    通过OpenCode CLI或API执行任务
    支持多种AI模型的通用适配器
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._进程: asyncio.subprocess.Process | None = None

    @property
    def 智能体ID(self) -> str:
        return "opencode"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "go", "rust"],
                上下文窗口=128000,
                每千令牌成本=0.001,
                最大并发任务数=3
            ),
            智能体能力(
                名称="code_review",
                语言列表=["python", "javascript", "typescript", "go", "rust"],
                上下文窗口=128000,
                每千令牌成本=0.001,
                最大并发任务数=3
            ),
            智能体能力(
                名称="exploration",
                语言列表=["python", "javascript", "typescript"],
                上下文窗口=128000,
                每千令牌成本=0.001,
                最大并发任务数=3
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.深度

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.便宜

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化OpenCode"""
        self._配置.update(配置)
        opencode_path = 配置.get("path", "opencode")
        logger.info(f"OpenCode适配器初始化 (路径: {opencode_path}, 模型: {self._模型})")

    async def 健康检查(self) -> bool:
        """检查OpenCode是否可用"""
        try:
            opencode_path = self._配置.get("path", "opencode")
            进程 = await asyncio.create_subprocess_exec(
                opencode_path, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(进程.communicate(), timeout=5)
            return 进程.returncode == 0
        except Exception as e:
            logger.error(f"OpenCode健康检查失败: {e}")
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
            opencode_path = self._配置.get("path", "opencode")

            进程 = await asyncio.create_subprocess_exec(
                opencode_path, "run",
                "--model", self._模型,
                "--prompt", 提示词,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self._进程 = 进程
            stdout, stderr = await asyncio.wait_for(
                进程.communicate(),
                timeout=self._配置.get("timeout", 300)
            )

            输出文本 = stdout.decode("utf-8", errors="replace")
            错误文本 = stderr.decode("utf-8", errors="replace")

            if 进程.returncode != 0:
                raise RuntimeError(f"OpenCode执行失败: {错误文本}")

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
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时毫秒,
                错误=None
            )

        except asyncio.TimeoutError:
            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)
            logger.error(f"任务 {任务ID} 执行超时")
            return 任务结果(
                任务ID=任务ID,
                状态="failed",
                输出数据={},
                制品列表=[],
                使用的令牌数=0,
                成本=0.0,
                耗时毫秒=耗时毫秒,
                错误="任务执行超时"
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
        opencode_path = self._配置.get("path", "opencode")

        进程 = await asyncio.create_subprocess_exec(
            opencode_path, "run",
            "--model", self._模型,
            "--prompt", 提示词,
            "--stream",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self._进程 = 进程

        async for 行 in 进程.stdout:
            文本 = 行.decode("utf-8", errors="replace").strip()
            if 文本:
                yield {"type": "text", "text": 文本}

        yield {"type": "done", "任务ID": 任务ID}

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        if self._进程:
            try:
                self._进程.terminate()
                logger.info(f"任务 {任务ID} 已取消")
                return True
            except Exception as e:
                logger.error(f"取消任务 {任务ID} 失败: {e}")
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
            "项目上下文": str(上下文.元数据) if 上下文 and 上下文.元数据 else "",
        }

        # 生成提示词
        提示词结果 = 模板管理器.生成提示词(模板名称, 上下文数据)

        if 提示词结果:
            return 提示词结果["用户提示词"]
        else:
            # 如果模板生成失败，使用默认提示词
            部分 = ["你是一个专业的软件开发助手。"]

            if 任务类型 == "code_generation":
                部分.append("请根据需求生成高质量的代码。")
            elif 任务类型 == "code_review":
                部分.append("请审查代码质量并提供改进建议。")
            elif 任务类型 == "exploration":
                部分.append("请分析代码库并提供详细的分析报告。")

            if 输入数据:
                部分.append("\n## 输入数据\n")
                for 键, 值 in 输入数据.items():
                    部分.append(f"**{键}**: {值}")

            return "\n".join(部分)

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
