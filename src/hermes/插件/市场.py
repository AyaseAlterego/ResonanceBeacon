"""插件市场"""
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
from enum import Enum
from urllib.parse import urlparse
import aiohttp
import json
import shutil
import logging
import semver
import zipfile
import hashlib
import io

from .系统 import 插件类型, 插件元数据, 插件管理器

logger = logging.getLogger(__name__)

class 插件状态(str, Enum):
    未安装 = "not_installed"
    已安装 = "installed"
    需更新 = "update_available"
    已加载 = "loaded"

@dataclass
class 市场插件信息:
    ID: str
    名称: str
    版本: str
    类型: 插件类型
    描述: str = ""
    作者: str = ""
    依赖项: list[str] = field(default_factory=list)
    配置模式: dict[str, Any] | None = None
    下载地址: str = ""
    源码地址: str = ""
    标签: list[str] = field(default_factory=list)
    下载次数: int = 0
    评分: float = 0.0
    哈希: str = ""

@dataclass
class 已安装插件信息:
    ID: str
    名称: str
    已安装版本: str
    最新版本: str
    状态: 插件状态
    安装时间: str = ""
    安装路径: str = ""

class 插件市场:
    def __init__(self, 插件管理器: 插件管理器, 市场索引地址: str = "", 本地缓存路径: str = "./插件市场缓存"):
        self.插件管理器 = 插件管理器
        self.市场索引地址 = 市场索引地址
        self.本地缓存路径 = Path(本地缓存路径)
        self.本地缓存路径.mkdir(parents=True, exist_ok=True)
        self._远程索引: list[市场插件信息] = []
        self._已安装状态: dict[str, 已安装插件信息] = {}
        self._本地索引路径 = self.本地缓存路径 / "索引.json"

    async def 加载远程索引(self) -> list[市场插件信息]:
        if self._远程索引:
            return self._远程索引

        本地索引 = self._加载本地索引()
        if 本地索引:
            self._远程索引 = 本地索引
            return self._远程索引

        if self.市场索引地址:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.市场索引地址) as response:
                        if response.status == 200:
                            数据 = await response.json()
                            self._远程索引 = [市场插件信息(**项) for 项 in 数据]
                            self._保存本地索引()
                            return self._远程索引
            except Exception as e:
                logger.error(f"加载远程索引失败: {e}")

        return self._远程索引

    def _加载本地索引(self) -> list[市场插件信息] | None:
        if not self._本地索引路径.exists():
            return None
        try:
            with open(self._本地索引路径, "r", encoding="utf-8") as f:
                数据 = json.load(f)
            return [市场插件信息(**项) for 项 in 数据]
        except Exception as e:
            logger.error(f"加载本地索引失败: {e}")
            return None

    def _保存本地索引(self) -> None:
        try:
            数据 = []
            for 信息 in self._远程索引:
                项 = {
                    "ID": 信息.ID,
                    "名称": 信息.名称,
                    "版本": 信息.版本,
                    "类型": 信息.类型.value if isinstance(信息.类型, 插件类型) else 信息.类型,
                    "描述": 信息.描述,
                    "作者": 信息.作者,
                    "依赖项": 信息.依赖项,
                    "配置模式": 信息.配置模式,
                    "下载地址": 信息.下载地址,
                    "源码地址": 信息.源码地址,
                    "标签": 信息.标签,
                    "下载次数": 信息.下载次数,
                    "评分": 信息.评分,
                }
                数据.append(项)
            with open(self._本地索引路径, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存本地索引失败: {e}")

    async def 搜索插件(self, 关键词: str = "", 类型: 插件类型 | None = None, 标签: str = "") -> list[市场插件信息]:
        索引 = await self.加载远程索引()
        结果 = []
        for 插件信息 in 索引:
            匹配 = True
            if 关键词:
                关键词小写 = 关键词.lower()
                名称匹配 = 关键词小写 in 插件信息.名称.lower()
                描述匹配 = 关键词小写 in 插件信息.描述.lower()
                ID匹配 = 关键词小写 in 插件信息.ID.lower()
                if not (名称匹配 or 描述匹配 or ID匹配):
                    匹配 = False
            if 类型 and 插件信息.类型 != 类型:
                匹配 = False
            if 标签 and 标签 not in 插件信息.标签:
                匹配 = False
            if 匹配:
                结果.append(插件信息)
        return 结果

    async def 获取可用插件列表(self) -> list[市场插件信息]:
        return await self.加载远程索引()

    async def 获取已安装插件(self) -> list[已安装插件信息]:
        await self._刷新已安装状态()
        return list(self._已安装状态.values())

    async def _刷新已安装状态(self) -> None:
        扫描结果 = await self.插件管理器.扫描插件()
        远程索引 = await self.加载远程索引()
        远程版本映射 = {信息.ID: 信息.版本 for 信息 in 远程索引}

        self._已安装状态.clear()
        for 元数据 in 扫描结果:
            最新版本 = 远程版本映射.get(元数据.ID, 元数据.版本)
            if 最新版本 != 元数据.版本:
                try:
                    if semver.compare(最新版本, 元数据.版本) > 0:
                        状态 = 插件状态.需更新
                    else:
                        状态 = 插件状态.已安装
                except ValueError:
                    状态 = 插件状态.已安装
            else:
                状态 = 插件状态.已安装

            if 元数据.ID in self.插件管理器._已加载插件:
                状态 = 插件状态.已加载

            插件目录 = self.插件管理器.插件路径 / 元数据.ID
            self._已安装状态[元数据.ID] = 已安装插件信息(
                ID=元数据.ID,
                名称=元数据.名称,
                已安装版本=元数据.版本,
                最新版本=最新版本,
                状态=状态,
                安装路径=str(插件目录),
            )

    async def 安装插件(self, 插件ID: str) -> dict[str, Any]:
        远程索引 = await self.加载远程索引()
        目标插件 = None
        for 信息 in 远程索引:
            if 信息.ID == 插件ID:
                目标插件 = 信息
                break

        if not 目标插件:
            return {"成功": False, "消息": f"在市场索引中未找到插件: {插件ID}"}

        if not 目标插件.依赖项:
            return await self._执行安装(目标插件)

        依赖结果 = await self._解析依赖(目标插件.依赖项)
        if not 依赖结果["满足"]:
            return {"成功": False, "消息": f"依赖不满足: {依赖结果['缺失']}"}

        for 依赖ID in 目标插件.依赖项:
            if 依赖ID not in self._已安装状态:
                依赖安装结果 = await self.安装插件(依赖ID)
                if not 依赖安装结果["成功"]:
                    return {"成功": False, "消息": f"安装依赖 {依赖ID} 失败: {依赖安装结果['消息']}"}

        return await self._执行安装(目标插件)

    async def _执行安装(self, 插件信息: 市场插件信息) -> dict[str, Any]:
        目标目录 = self.插件管理器.插件路径 / 插件信息.ID
        if 目标目录.exists():
            return {"成功": False, "消息": f"插件已安装: {插件信息.ID}"}

        try:
            if 插件信息.下载地址:
                async with aiohttp.ClientSession() as session:
                    async with session.get(插件信息.下载地址) as response:
                        if response.status != 200:
                            return {"成功": False, "消息": f"下载插件失败: HTTP {response.status}"}
                        内容 = await response.read()
                缓存路径 = self.本地缓存路径 / f"{插件信息.ID}.zip"
                with open(缓存路径, "wb") as f:
                    f.write(内容)
                shutil.unpack_archive(str(缓存路径), str(目标目录))
            else:
                目标目录.mkdir(parents=True, exist_ok=True)
                配置 = {
                    "ID": 插件信息.ID,
                    "名称": 插件信息.名称,
                    "版本": 插件信息.版本,
                    "类型": 插件信息.类型.value if isinstance(插件信息.类型, 插件类型) else 插件信息.类型,
                    "描述": 插件信息.描述,
                    "作者": 插件信息.作者,
                    "依赖项": 插件信息.依赖项,
                }
                with open(目标目录 / "插件配置.json", "w", encoding="utf-8") as f:
                    json.dump(配置, f, ensure_ascii=False, indent=2)
                with open(目标目录 / "__init__.py", "w", encoding="utf-8") as f:
                    f.write("from src.hermes.插件.系统 import 插件接口, 插件元数据, 插件类型\n\n")
                    f.write(f"class 插件类(插件接口):\n")
                    f.write(f"    @property\n")
                    f.write(f"    def 元数据(self) -> 插件元数据:\n")
                    f.write(f"        return 插件元数据(ID=\"{插件信息.ID}\", 名称=\"{插件信息.名称}\", 版本=\"{插件信息.版本}\", 类型=插件类型.{插件信息.类型.name if isinstance(插件信息.类型, 插件类型) else 插件信息.类型}, 描述=\"{插件信息.描述}\")\n\n")
                    f.write(f"    async def 初始化(self, 配置: dict) -> None:\n")
                    f.write(f"        pass\n\n")
                    f.write(f"    async def 卸载(self) -> None:\n")
                    f.write(f"        pass\n")
                with open(目标目录 / "配置.json", "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)

            await self._刷新已安装状态()
            logger.info(f"安装插件: {插件信息.ID} v{插件信息.版本}")
            return {"成功": True, "消息": f"插件 {插件信息.ID} 安装成功"}
        except Exception as e:
            logger.error(f"安装插件 {插件信息.ID} 失败: {e}", exc_info=True)
            if 目标目录.exists():
                shutil.rmtree(str(目标目录))
            return {"成功": False, "消息": f"安装失败: {e}"}

    async def _解析依赖(self, 依赖项: list[str]) -> dict[str, Any]:
        await self._刷新已安装状态()
        缺失 = []
        for 依赖ID in 依赖项:
            if 依赖ID not in self._已安装状态:
                远程索引 = await self.加载远程索引()
                存在于远程 = any(信息.ID == 依赖ID for 信息 in 远程索引)
                if 存在于远程:
                    缺失.append(依赖ID)
                else:
                    return {"满足": False, "缺失": [依赖ID], "消息": f"依赖 {依赖ID} 在市场中不可用"}

        if 缺失:
            return {"满足": False, "缺失": 缺失, "消息": f"缺少依赖: {缺失}"}

        return {"满足": True, "缺失": [], "消息": "依赖满足"}

    async def 卸载插件(self, 插件ID: str) -> dict[str, Any]:
        if 插件ID in self.插件管理器._已加载插件:
            卸载结果 = await self.插件管理器.卸载插件(插件ID)
            if not 卸载结果:
                return {"成功": False, "消息": f"卸载已加载插件 {插件ID} 失败"}

        插件目录 = self.插件管理器.插件路径 / 插件ID
        if not 插件目录.exists():
            return {"成功": False, "消息": f"插件目录不存在: {插件ID}"}

        try:
            shutil.rmtree(str(插件目录))
            self._已安装状态.pop(插件ID, None)
            logger.info(f"卸载插件: {插件ID}")
            return {"成功": True, "消息": f"插件 {插件ID} 已卸载"}
        except Exception as e:
            logger.error(f"卸载插件 {插件ID} 失败: {e}")
            return {"成功": False, "消息": f"卸载失败: {e}"}

    async def 更新插件(self, 插件ID: str) -> dict[str, Any]:
        await self._刷新已安装状态()
        安装信息 = self._已安装状态.get(插件ID)
        if not 安装信息:
            return {"成功": False, "消息": f"插件未安装: {插件ID}"}

        远程索引 = await self.加载远程索引()
        远程插件 = None
        for 信息 in 远程索引:
            if 信息.ID == 插件ID:
                远程插件 = 信息
                break

        if not 远程插件:
            return {"成功": False, "消息": f"在市场索引中未找到插件: {插件ID}"}

        try:
            最新版本 = 远程插件.版本
            当前版本 = 安装信息.已安装版本
            if semver.compare(最新版本, 当前版本) <= 0:
                return {"成功": False, "消息": f"插件已是最新版本: {当前版本}"}
        except ValueError:
            pass

        卸载结果 = await self.卸载插件(插件ID)
        if not 卸载结果["成功"]:
            return 卸载结果

        安装结果 = await self._执行安装(远程插件)
        if 安装结果["成功"]:
            安装结果["消息"] = f"插件 {插件ID} 已从 {安装信息.已安装版本} 更新到 {远程插件.版本}"
        return 安装结果

    async def 获取插件详情(self, 插件ID: str) -> 市场插件信息 | None:
        索引 = await self.加载远程索引()
        for 信息 in 索引:
            if 信息.ID == 插件ID:
                return 信息
        return None

    def 加载本地索引文件(self, 文件路径: str) -> list[市场插件信息]:
        try:
            with open(文件路径, "r", encoding="utf-8") as f:
                数据 = json.load(f)
            self._远程索引 = [市场插件信息(**项) for 项 in 数据]
            self._保存本地索引()
            return self._远程索引
        except Exception as e:
            logger.error(f"加载本地索引文件失败: {e}")
            return []
