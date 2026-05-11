"""多层级配置加载器，支持closest-wins策略"""
import json5
import os
from pathlib import Path
from typing import Optional
import logging

from .模式 import 应用配置
from .合并 import 安全深度合并多层, 检查原型污染

logger = logging.getLogger(__name__)

class 配置加载器:
    """
    多层级配置加载器

    配置优先级（从最不具体到最具体）：
    1. 默认值（代码内）
    2. /etc/hermes/配置.jsonc
    3. ~/.hermes/配置.jsonc
    4. <父目录>/.hermes/配置.jsonc
    5. <项目>/.hermes/配置.jsonc

    使用closest-wins策略：越接近项目的配置越优先
    """

    def __init__(self, 配置目录名称: str = ".hermes", 配置文件名: str = "配置.jsonc"):
        self.配置目录名称 = 配置目录名称
        self.配置文件名 = 配置文件名
        self._缓存: Optional[应用配置] = None

    def 加载配置(
        self,
        环境: Optional[str] = None,
        项目路径: Optional[Path] = None
    ) -> 应用配置:
        """
        加载合并后的配置

        Args:
            环境: 环境名称（development/production）
            项目路径: 项目根目录路径

        Returns:
            合并后的应用配置
        """
        if self._缓存 is not None:
            return self._缓存

        # 从不同层级收集配置
        配置层级 = []

        # 1. 默认值
        默认配置 = self._加载默认配置()
        配置层级.append(默认配置)

        # 2. 系统级配置
        系统配置 = self._加载系统配置()
        if 系统配置:
            配置层级.append(系统配置)

        # 3. 用户级配置
        用户配置 = self._加载用户配置()
        if 用户配置:
            配置层级.append(用户配置)

        # 4. 项目级配置（从当前目录到HOME的所有配置）
        项目路径 = 项目路径 or Path.cwd()
        项目配置列表 = self._加载项目级配置(项目路径)
        配置层级.extend(项目配置列表)

        # 合并所有配置
        if len(配置层级) > 1:
            合并后的字典 = 安全深度合并多层([层.model_dump() for 层 in 配置层级])
        else:
            合并后的字典 = 配置层级[0].model_dump()

        # 应用环境变量覆盖
        合并后的字典 = self._应用环境变量覆盖(合并后的字典)

        # 创建最终配置对象
        最终配置 = 应用配置(**合并后的字典)

        # 缓存结果
        self._缓存 = 最终配置

        logger.info(f"配置加载完成，使用了 {len(配置层级)} 个配置层级")
        return 最终配置

    def _加载默认配置(self) -> 应用配置:
        """加载默认配置"""
        return 应用配置()

    def _加载系统配置(self) -> Optional[应用配置]:
        """加载系统级配置（/etc/hermes/配置.jsonc）"""
        系统配置路径 = Path("/etc") / self.配置目录名称 / self.配置文件名
        return self._从文件加载配置(系统配置路径)

    def _加载用户配置(self) -> Optional[应用配置]:
        """加载用户级配置（~/.hermes/配置.jsonc）"""
        用户配置路径 = Path.home() / self.配置目录名称 / self.配置文件名
        return self._从文件加载配置(用户配置路径)

    def _加载项目级配置(self, 项目路径: Path) -> list[应用配置]:
        """
        加载项目级配置

        从当前目录向上遍历，直到HOME目录，
        收集所有找到的配置文件（closest-wins）
        """
        配置列表 = []
        当前路径 = 项目路径.resolve()
        HOME路径 = Path.home().resolve()

        while True:
            配置路径 = 当前路径 / self.配置目录名称 / self.配置文件名
            配置 = self._从文件加载配置(配置路径)
            if 配置:
                配置列表.append(配置)

            # 如果到达HOME目录，停止
            if 当前路径 == HOME路径:
                break

            # 向上一级
            父路径 = 当前路径.parent
            if 父路径 == 当前路径:  # 到达根目录
                break
            当前路径 = 父路径

        # 反转列表，使最接近项目的配置最后合并（closest-wins）
        配置列表.reverse()
        return 配置列表

    def _从文件加载配置(self, 配置路径: Path) -> Optional[应用配置]:
        """从文件加载配置"""
        if not 配置路径.exists():
            return None

        try:
            内容 = 配置路径.read_text(encoding="utf-8")

            配置字典 = json5.loads(内容)

            危险键 = 检查原型污染(配置字典)
            if 危险键:
                raise ValueError(f"在配置文件 {配置路径} 中发现潜在的原型污染: {危险键}")

            return 应用配置(**配置字典)

        except json5.JSONDecodeError as e:
            logger.error(f"解析配置文件 {配置路径} 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"加载配置文件 {配置路径} 失败: {e}")
            return None

    def _应用环境变量覆盖(self, 配置字典: dict) -> dict:
        """
        应用环境变量覆盖

        支持的环境变量格式：
        - HERMES_环境=development
        - HERMES_数据库URL=postgresql://...
        - HERMES_智能体_claude_code_模型=claude-3-opus
        """
        环境变量映射 = {
            "HERMES_环境": "环境",
            "HERMES_数据库URL": "数据库URL",
            "HERMES_REDISURL": "RedisURL",
        }

        for 环境变量, 配置键 in 环境变量映射.items():
            值 = os.getenv(环境变量)
            if 值 is not None:
                配置字典[配置键] = 值
                logger.debug(f"使用环境变量 {环境变量} 覆盖配置 {配置键}")

        # 处理智能体配置的环境变量
        # 格式：HERMES_智能体_<agent_id>_<field>=<value>
        for 环境变量, 值 in os.environ.items():
            if 环境变量.startswith("HERMES_智能体_"):
                前缀 = "HERMES_智能体_"
                部分 = 环境变量[len(前缀):].split('_', 1)
                if len(部分) == 2:
                    智能体ID, 字段名 = 部分
                    智能体ID = 智能体ID.lower()
                    if "智能体" not in 配置字典:
                        配置字典["智能体"] = {}
                    if 智能体ID not in 配置字典["智能体"]:
                        配置字典["智能体"][智能体ID] = {}
                    配置字典["智能体"][智能体ID][字段名] = 值
                    logger.debug(f"使用环境变量覆盖智能体配置: {智能体ID}.{字段名}")

        return 配置字典

    def 清除缓存(self):
        """清除配置缓存"""
        self._缓存 = None

    def 重新加载配置(self, 环境: Optional[str] = None, 项目路径: Optional[Path] = None) -> 应用配置:
        """强制重新加载配置"""
        self.清除缓存()
        return self.加载配置(环境, 项目路径)

# 全局配置加载器实例
配置加载器实例 = 配置加载器()

def 获取配置() -> 应用配置:
    """获取全局配置"""
    return 配置加载器实例.加载配置()
