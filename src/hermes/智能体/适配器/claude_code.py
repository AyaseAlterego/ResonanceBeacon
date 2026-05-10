"""Claude Code适配器实现"""
import time
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

class ClaudeCode适配器(智能体适配器):
    """
    Claude Code适配器

    通过Claude API执行任务
    """

    def __init__(self, 模型: str, 配置: dict[str, Any]):
        self._模型 = 模型
        self._配置 = 配置
        self._客户端 = None  # Anthropic客户端

    @property
    def 智能体ID(self) -> str:
        return "claude_code"

    @property
    def 能力列表(self) -> list[智能体能力]:
        return [
            智能体能力(
                名称="code_generation",
                语言列表=["python", "javascript", "typescript", "java", "go"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="requirements_engineering",
                语言列表=["markdown", "json", "yaml"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="architecture_design",
                语言列表=["markdown", "diagrams"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
            智能体能力(
                名称="code_review",
                语言列表=["python", "javascript", "typescript", "java", "go"],
                上下文窗口=200000,
                每千令牌成本=0.003,
                最大并发任务数=5
            ),
        ]

    @property
    def 类别(self) -> 智能体类别:
        return 智能体类别.超级大脑

    @property
    def 成本层级(self) -> 智能体成本:
        return 智能体成本.昂贵

    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化Claude API客户端"""
        try:
            import anthropic
            self._客户端 = anthropic.AsyncAnthropic(
                api_key=配置.get("api_key")
            )
            logger.info(f"Claude Code适配器初始化成功 (模型: {self._模型})")
        except ImportError:
            logger.error("未安装anthropic库，请运行: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"初始化Claude API客户端失败: {e}")
            raise

    async def 健康检查(self) -> bool:
        """执行健康检查"""
        try:
            if not self._客户端:
                return False

            # 简单的API调用测试
            响应 = await self._客户端.messages.create(
                model=self._模型,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.error(f"Claude Code健康检查失败: {e}")
            return False

    async def 执行任务(
        self,
        任务ID: str,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> 任务结果:
        """
        执行单个任务

        Args:
            任务ID: 任务唯一标识
            任务类型: 任务类型（如 "code_generation", "requirements_engineering"）
            输入数据: 输入数据
            上下文: 上下文信息

        Returns:
            任务执行结果
        """
        开始时间 = time.time()

        try:
            # 构建提示词
            提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

            # 调用Claude API
            响应 = await self._客户端.messages.create(
                model=self._模型,
                max_tokens=self._配置.get("max_tokens", 4096),
                messages=[{"role": "user", "content": 提示词}]
            )

            # 解析响应
            输出文本 = 响应.content[0].text if 响应.content else ""

            # 提取使用信息
            使用的令牌数 = 响应.usage.input_tokens + 响应.usage.output_tokens
            成本 = self._计算成本(响应.usage)

            # 提取制品（如果响应中包含代码或文档）
            制品 = self._提取制品(输出文本, 任务类型)

            结束时间 = time.time()
            耗时毫秒 = int((结束时间 - 开始时间) * 1000)

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
        """
        流式执行任务

        Yields:
            增量结果字典
        """
        # 构建提示词
        提示词 = self._构建提示词(任务类型, 输入数据, 上下文)

        # 流式调用Claude API
        async with self._客户端.messages.stream(
            model=self._模型,
            max_tokens=self._配置.get("max_tokens", 4096),
            messages=[{"role": "user", "content": 提示词}]
        ) as 流:
            async for 文本 in 流.text_stream:
                yield {
                    "type": "text",
                    "text": 文本
                }

        # 完成
        yield {
            "type": "done",
            "任务ID": 任务ID
        }

    async def 取消任务(self, 任务ID: str) -> bool:
        """取消任务"""
        # Claude API目前不支持取消操作
        logger.warning(f"Claude Code适配器不支持取消任务 {任务ID}")
        return False

    def _构建提示词(
        self,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> str:
        """根据任务类型构建提示词"""
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
            "文档类型": 输入数据.get("文档类型", "API文档"),
            "内容描述": 输入数据.get("内容", ""),
            "目标受众": 输入数据.get("受众", "开发者"),
            "系统需求": 输入数据.get("系统需求", ""),
            "技术约束": 输入数据.get("技术约束", ""),
            "预期规模": 输入数据.get("预期规模", "中等"),
            "原始需求": 输入数据.get("原始需求", ""),
            "项目背景": 输入数据.get("项目背景", ""),
            "利益相关者": 输入数据.get("利益相关者", ""),
            "测试框架": 输入数据.get("测试框架", "pytest"),
        }

        # 生成提示词
        提示词结果 = 模板管理器.生成提示词(模板名称, 上下文数据)

        if 提示词结果:
            return 提示词结果["用户提示词"]
        else:
            # 如果模板生成失败，使用默认提示词
            return self._生成默认提示词(任务类型, 输入数据, 上下文)

    def _生成默认提示词(
        self,
        任务类型: str,
        输入数据: dict[str, Any],
        上下文: 上下文包
    ) -> str:
        """生成默认提示词（模板系统的后备方案）"""
        提示词部分 = ["你是一个专业的软件开发助手。"]

        if 任务类型 == "code_generation":
            提示词部分.append("请根据需求生成代码。")
        elif 任务类型 == "code_review":
            提示词部分.append("请审查代码质量。")
        elif 任务类型 == "test_generation":
            提示词部分.append("请生成测试用例。")
        else:
            提示词部分.append("请完成指定的任务。")

        # 添加输入数据
        if 输入数据:
            提示词部分.append("\n输入数据：")
            for 键, 值 in 输入数据.items():
                提示词部分.append(f"{键}: {值}")

        return "\n".join(提示词部分)

    def _计算成本(self, 使用量) -> float:
        """计算API调用成本"""
        # Claude 3.5 Sonnet定价（示例）
        输入成本 = 使用量.input_tokens * 0.003 / 1000
        输出成本 = 使用量.output_tokens * 0.015 / 1000
        return 输入成本 + 输出成本

    def _提取制品(self, 输出文本: str, 任务类型: str) -> list[dict]:
        """从输出文本中提取制品"""
        制品 = []

        # 简单的代码块提取
        if "```" in 输出文本:
            代码块 = []
            在代码块中 = False

            for 行 in 输出文本.split("\n"):
                if 行.startswith("```"):
                    在代码块中 = not 在代码块中
                    if not 在代码块中 and 代码块:
                        代码 = "\n".join(代码块)
                        制品.append({
                            "类型": "code",
                            "内容": 代码,
                            "语言": "unknown"  # 可以从```后面的语言标识提取
                        })
                        代码块 = []
                elif 在代码块中:
                    代码块.append(行)

        return 制品
