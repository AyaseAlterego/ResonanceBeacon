"""智能体注册表"""
from typing import Optional
import logging

from .基础 import 智能体适配器, 智能体工厂, 安全创建适配器

logger = logging.getLogger(__name__)

class 智能体注册表:
    """
    智能体注册表

    管理所有可用的智能体，提供智能体发现、注册和查询功能
    """

    def __init__(self):
        self._智能体工厂: dict[str, 智能体工厂] = {}
        self._已注册智能体: dict[str, 智能体适配器] = {}
        self._智能体配置: dict[str, dict] = {}

    def 注册工厂(self, 工厂: 智能体工厂):
        """注册智能体工厂"""
        self._智能体工厂[工厂.智能体ID] = 工厂
        logger.info(f"注册智能体工厂: {工厂.智能体ID}")

    def 注册智能体(self, 智能体: 智能体适配器):
        """直接注册智能体实例"""
        self._已注册智能体[智能体.智能体ID] = 智能体
        logger.info(f"注册智能体实例: {智能体.智能体ID}")

    def 设置配置(self, 智能体ID: str, 配置: dict):
        """设置智能体配置"""
        self._智能体配置[智能体ID] = 配置

    def 获取智能体(self, 智能体ID: str) -> Optional[智能体适配器]:
        """获取智能体实例"""
        # 首先检查已注册的实例
        if 智能体ID in self._已注册智能体:
            return self._已注册智能体[智能体ID]

        # 如果没有，尝试从工厂创建
        if 智能体ID in self._智能体工厂:
            工厂 = self._智能体工厂[智能体ID]
            配置 = self._智能体配置.get(智能体ID, {})
            模型 = 配置.get("模型", "default")

            # 使用安全创建
            适配器 = 安全创建适配器(工厂, 模型, 配置)
            if 适配器:
                self._已注册智能体[智能体ID] = 适配器
                return 适配器

        return None

    def 获取所有智能体ID(self) -> list[str]:
        """获取所有已注册的智能体ID"""
        所有ID = set(self._智能体工厂.keys())
        所有ID.update(self._已注册智能体.keys())
        return list(所有ID)

    def 获取所有健康智能体(self) -> list[智能体适配器]:
        """获取所有健康的智能体"""
        健康智能体 = []
        for 智能体ID in self.获取所有智能体ID():
            智能体 = self.获取智能体(智能体ID)
            if 智能体:
                # 这里可以添加健康检查逻辑
                健康智能体.append(智能体)
        return 健康智能体

    async def 初始化所有智能体(self):
        """初始化所有已注册的智能体"""
        for 智能体ID, 工厂 in self._智能体工厂.items():
            配置 = self._智能体配置.get(智能体ID, {})
            模型 = 配置.get("模型", "default")

            适配器 = 安全创建适配器(工厂, 模型, 配置)
            if 适配器:
                try:
                    await 适配器.初始化(配置)
                    self._已注册智能体[智能体ID] = 适配器
                    logger.info(f"成功初始化智能体: {智能体ID}")
                except Exception as e:
                    logger.error(f"初始化智能体 {智能体ID} 失败: {e}")
            else:
                logger.warning(f"无法创建智能体 {智能体ID}")

    async def 健康检查所有智能体(self) -> dict[str, bool]:
        """对所有智能体执行健康检查"""
        结果 = {}
        for 智能体ID in self.获取所有智能体ID():
            智能体 = self.获取智能体(智能体ID)
            if 智能体:
                try:
                    健康 = await 智能体.健康检查()
                    结果[智能体ID] = 健康
                except Exception as e:
                    logger.error(f"智能体 {智能体ID} 健康检查失败: {e}")
                    结果[智能体ID] = False
            else:
                结果[智能体ID] = False
        return 结果

    def 获取智能体数量(self) -> int:
        """获取已注册的智能体数量"""
        return len(self.获取所有智能体ID())

    def __repr__(self) -> str:
        return f"<智能体注册表: {self.获取智能体数量()} 个智能体>"
