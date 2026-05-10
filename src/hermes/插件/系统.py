"""插件系统"""
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any, Callable
from enum import Enum
from pathlib import Path
import importlib
import logging
import json

logger = logging.getLogger(__name__)

class 插件类型(str, Enum):
    """插件类型"""
    智能体 = "agent"
    阶段 = "stage"
    钩子 = "hook"
    制品存储 = "artifact_store"
    通知 = "notification"

@dataclass
class 插件元数据:
    """插件元数据"""
    ID: str
    名称: str
    版本: str
    类型: 插件类型
    描述: str = ""
    作者: str = ""
    依赖项: list[str] = field(default_factory=list)
    配置模式: dict[str, Any] | None = None

class 插件接口(ABC):
    """插件接口抽象基类"""

    @property
    @abstractmethod
    def 元数据(self) -> 插件元数据:
        """插件元数据"""
        pass

    @abstractmethod
    async def 初始化(self, 配置: dict[str, Any]) -> None:
        """初始化插件"""
        pass

    @abstractmethod
    async def 卸载(self) -> None:
        """卸载插件"""
        pass

class 智能体插件接口(插件接口):
    """智能体插件接口"""

    @abstractmethod
    def 获取适配器类(self) -> type:
        """获取智能体适配器类"""
        pass

class 阶段插件接口(插件接口):
    """阶段插件接口"""

    @abstractmethod
    def 获取阶段处理器(self) -> Callable:
        """获取阶段处理器"""
        pass

class 钩子插件接口(插件接口):
    """钩子插件接口"""

    @abstractmethod
    def 获取钩子列表(self) -> list[dict[str, Any]]:
        """获取钩子定义列表"""
        pass

class 插件管理器:
    """
    插件管理器

    负责插件的发现、加载、初始化和管理
    """

    def __init__(self, 插件路径: str = "./插件"):
        self.插件路径 = Path(插件路径)
        self.插件路径.mkdir(parents=True, exist_ok=True)

        self._已加载插件: dict[str, 插件接口] = {}
        self._插件元数据: dict[str, 插件元数据] = {}

    async def 扫描插件(self) -> list[插件元数据]:
        """扫描插件目录"""
        发现的插件 = []

        for 插件目录 in self.插件路径.iterdir():
            if 插件目录.is_dir():
                配置文件 = 插件目录 / "插件配置.json"
                if 配置文件.exists():
                    try:
                        with open(配置文件, "r", encoding="utf-8") as f:
                            配置 = json.load(f)
                        元数据 = 插件元数据(**配置)
                        发现的插件.append(元数据)
                    except Exception as e:
                        logger.error(f"加载插件配置失败 {插件目录}: {e}")

        return 发现的插件

    async def 加载插件(self, 插件ID: str) -> 插件接口 | None:
        """加载插件"""
        if 插件ID in self._已加载插件:
            return self._已加载插件[插件ID]

        插件目录 = self.插件路径 / 插件ID
        if not 插件目录.exists():
            logger.error(f"插件目录不存在: {插件目录}")
            return None

        try:
            # 动态导入插件模块
            模块路径 = 插件目录 / "__init__.py"
            if not 模块路径.exists():
                模块路径 = 插件目录 / f"{插件ID}.py"

            if not 模块路径.exists():
                logger.error(f"插件入口文件不存在: {插件目录}")
                return None

            # 导入模块
            规范名称 = f"插件.{插件ID}"
            规范路径 = str(插件目录)
            规格 = importlib.util.spec_from_file_location(
                规范名称,
                模块路径,
                submodule_search_locations=[规范路径]
            )

            if 规格 and 规格.loader:
                模块 = importlib.util.module_from_spec(规格)
                importlib.util.spec = 规格
                规格.loader.exec_module(模块)

                # 查找插件类
                if hasattr(模块, "插件类"):
                    插件类 = 模块.插件类
                    插件实例 = 插件类()

                    # 初始化插件
                    配置文件 = 插件目录 / "配置.json"
                    配置 = {}
                    if 配置文件.exists():
                        with open(配置文件, "r", encoding="utf-8") as f:
                            配置 = json.load(f)

                    await 插件实例.初始化(配置)

                    self._已加载插件[插件ID] = 插件实例
                    self._插件元数据[插件ID] = 插件实例.元数据

                    logger.info(f"加载插件: {插件ID} v{插件实例.元数据.版本}")
                    return 插件实例

        except Exception as e:
            logger.error(f"加载插件 {插件ID} 失败: {e}", exc_info=True)

        return None

    async def 卸载插件(self, 插件ID: str) -> bool:
        """卸载插件"""
        插件 = self._已加载插件.get(插件ID)
        if not 插件:
            return False

        try:
            await 插件.卸载()
            del self._已加载插件[插件ID]
            del self._插件元数据[插件ID]
            logger.info(f"卸载插件: {插件ID}")
            return True
        except Exception as e:
            logger.error(f"卸载插件 {插件ID} 失败: {e}")
            return False

    def 获取插件(self, 插件ID: str) -> 插件接口 | None:
        """获取已加载的插件"""
        return self._已加载插件.get(插件ID)

    def 获取所有插件(self) -> dict[str, 插件接口]:
        """获取所有已加载的插件"""
        return dict(self._已加载插件)

    def 获取插件元数据(self, 插件ID: str) -> 插件元数据 | None:
        """获取插件元数据"""
        return self._插件元数据.get(插件ID)

    def 按类型获取插件(self, 类型: 插件类型) -> list[插件接口]:
        """按类型获取插件"""
        return [
            插件 for 插件 in self._已加载插件.values()
            if 插件.元数据.类型 == 类型
        ]
