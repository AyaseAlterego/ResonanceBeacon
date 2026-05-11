"""制品存储"""
import os
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, BinaryIO, Optional
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class 制品元数据:
    """制品元数据"""
    ID: str
    名称: str
    类型: str
    流水线ID: str
    阶段ID: str | None = None
    任务ID: str | None = None
    文件路径: str = ""
    内容哈希: str = ""
    大小字节: int = 0
    MIME类型: str = ""
    创建时间: datetime | None = None
    元数据: dict[str, Any] | None = None

    def __post_init__(self):
        if self.创建时间 is None:
            self.创建时间 = datetime.now()
        if self.元数据 is None:
            self.元数据 = {}

class 本地制品存储:
    """
    本地制品存储

    基于文件系统的制品存储，适用于开发和测试
    """

    def __init__(self, 存储路径: str = "./制品"):
        self.存储路径 = Path(存储路径)
        self.存储路径.mkdir(parents=True, exist_ok=True)

        # 制品索引
        self._索引: dict[str, 制品元数据] = {}
        self._索引文件 = self.存储路径 / ".索引.json"
        self._加载索引()

    def _加载索引(self):
        """加载制品索引"""
        if self._索引文件.exists():
            try:
                with open(self._索引文件, "r", encoding="utf-8") as f:
                    数据 = json.load(f)
                    for ID, 元数据字典 in 数据.items():
                        元数据字典["创建时间"] = datetime.fromisoformat(元数据字典["创建时间"])
                        self._索引[ID] = 制品元数据(**元数据字典)
                logger.debug(f"加载了 {len(self._索引)} 个制品索引")
            except Exception as e:
                logger.error(f"加载制品索引失败: {e}")

    def _保存索引(self):
        """保存制品索引"""
        数据 = {}
        for ID, 元数据 in self._索引.items():
            元数据字典 = {
                "ID": 元数据.ID,
                "名称": 元数据.名称,
                "类型": 元数据.类型,
                "流水线ID": 元数据.流水线ID,
                "阶段ID": 元数据.阶段ID,
                "任务ID": 元数据.任务ID,
                "文件路径": 元数据.文件路径,
                "内容哈希": 元数据.内容哈希,
                "大小字节": 元数据.大小字节,
                "MIME类型": 元数据.MIME类型,
                "创建时间": 元数据.创建时间.isoformat(),
                "元数据": 元数据.元数据
            }
            数据[ID] = 元数据字典

        try:
            with open(self._索引文件, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存制品索引失败: {e}")

    def _校验路径安全(self, 名称: str) -> str:
        安全名称 = 名称.replace('\\', '/').split('/')[-1]
        if 安全名称 != 名称:
            logger.warning(f"检测到路径穿越尝试，已截断: {名称} -> {安全名称}")
        if '..' in 安全名称 or 安全名称.startswith('/') or 安全名称.startswith('\\'):
            raise ValueError(f"非法的文件名: {名称}")
        return 安全名称

    def 存储制品(
        self,
        名称: str,
        类型: str,
        流水线ID: str,
        内容: bytes | str,
        阶段ID: str | None = None,
        任务ID: str | None = None,
        MIME类型: str = "",
        元数据: dict[str, Any] | None = None
    ) -> 制品元数据:
        """
        存储制品

        Returns:
            制品元数据
        """
        from uuid import uuid4
        制品ID = str(uuid4())
        名称 = self._校验路径安全(名称)

        # 计算内容哈希
        if isinstance(内容, str):
            内容字节 = 内容.encode("utf-8")
        else:
            内容字节 = 内容

        内容哈希 = hashlib.sha256(内容字节).hexdigest()

        # 确定文件路径
        子目录 = self.存储路径 / 流水线ID
        子目录.mkdir(exist_ok=True)
        文件名 = f"{制品ID}_{名称}"
        文件路径 = 子目录 / 文件名

        # 写入文件
        with open(文件路径, "wb") as f:
            f.write(内容字节)

        # 创建元数据
        元数据对象 = 制品元数据(
            ID=制品ID,
            名称=名称,
            类型=类型,
            流水线ID=流水线ID,
            阶段ID=阶段ID,
            任务ID=任务ID,
            文件路径=str(文件路径.relative_to(self.存储路径)),
            内容哈希=内容哈希,
            大小字节=len(内容字节),
            MIME类型=MIME类型,
            元数据=元数据 or {}
        )

        self._索引[制品ID] = 元数据对象
        self._保存索引()

        logger.info(f"制品已存储: {制品ID} ({名称}, {len(内容字节)} bytes)")
        return 元数据对象

    def 获取制品(self, 制品ID: str) -> tuple[bytes, 制品元数据] | None:
        """
        获取制品

        Returns:
            (内容字节, 元数据) 或 None
        """
        元数据 = self._索引.get(制品ID)
        if not 元数据:
            return None

        文件路径 = self.存储路径 / 元数据.文件路径
        if not 文件路径.exists():
            logger.error(f"制品文件不存在: {文件路径}")
            return None

        with open(文件路径, "rb") as f:
            内容 = f.read()

        return 内容, 元数据

    def 获取制品元数据(self, 制品ID: str) -> 制品元数据 | None:
        """获取制品元数据"""
        return self._索引.get(制品ID)

    def 搜索制品(
        self,
        流水线ID: str | None = None,
        类型: str | None = None,
        任务ID: str | None = None
    ) -> list[制品元数据]:
        """搜索制品"""
        结果 = []

        for 元数据 in self._索引.values():
            if 流水线ID and 元数据.流水线ID != 流水线ID:
                continue
            if 类型 and 元数据.类型 != 类型:
                continue
            if 任务ID and 元数据.任务ID != 任务ID:
                continue
            结果.append(元数据)

        return sorted(结果, key=lambda x: x.创建时间 or datetime.min, reverse=True)

    def 删除制品(self, 制品ID: str) -> bool:
        """删除制品"""
        元数据 = self._索引.get(制品ID)
        if not 元数据:
            return False

        文件路径 = self.存储路径 / 元数据.文件路径
        if 文件路径.exists():
            文件路径.unlink()

        del self._索引[制品ID]
        self._保存索引()

        logger.info(f"制品已删除: {制品ID}")
        return True

    def 获取存储统计(self) -> dict[str, Any]:
        """获取存储统计"""
        总大小 = sum(元数据.大小字节 for 元数据 in self._索引.values())
        总制品数 = len(self._索引)

        类型统计 = {}
        for 元数据 in self._索引.values():
            类型统计[元数据.类型] = 类型统计.get(元数据.类型, 0) + 1

        return {
            "总制品数": 总制品数,
            "总大小字节": 总大小,
            "总大小MB": round(总大小 / 1024 / 1024, 2),
            "类型统计": 类型统计
        }
