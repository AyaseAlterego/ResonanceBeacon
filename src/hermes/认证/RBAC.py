"""基于角色的访问控制（RBAC）"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import logging
import hashlib
import secrets
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class 角色(str, Enum):
    """系统角色"""
    管理员 = "admin"
    项目所有者 = "project_owner"
    开发者 = "developer"
    查看者 = "viewer"

class 权限(str, Enum):
    """系统权限"""
    项目_创建 = "project:create"
    项目_读取 = "project:read"
    项目_更新 = "project:update"
    项目_删除 = "project:delete"
    流水线_创建 = "pipeline:create"
    流水线_读取 = "pipeline:read"
    流水线_运行 = "pipeline:run"
    流水线_取消 = "pipeline:cancel"
    审批_查看 = "approval:view"
    审批_决策 = "approval:decide"
    智能体_查看 = "agent:view"
    智能体_管理 = "agent:manage"
    配置_查看 = "config:view"
    配置_更新 = "config:update"
    监控_查看 = "monitor:view"
    制品_读取 = "artifact:read"
    制品_下载 = "artifact:download"
    用户_管理 = "user:manage"

# 角色权限映射
角色权限映射: dict[角色, set[权限]] = {
    角色.管理员: set(权限),  # 所有权限
    角色.项目所有者: {
        权限.项目_创建, 权限.项目_读取, 权限.项目_更新, 权限.项目_删除,
        权限.流水线_创建, 权限.流水线_读取, 权限.流水线_运行, 权限.流水线_取消,
        权限.审批_查看, 权限.审批_决策,
        权限.智能体_查看, 权限.配置_查看,
        权限.监控_查看, 权限.制品_读取, 权限.制品_下载,
    },
    角色.开发者: {
        权限.项目_读取,
        权限.流水线_创建, 权限.流水线_读取, 权限.流水线_运行,
        权限.审批_查看,
        权限.智能体_查看, 权限.配置_查看,
        权限.制品_读取, 权限.制品_下载,
    },
    角色.查看者: {
        权限.项目_读取,
        权限.流水线_读取,
        权限.审批_查看,
        权限.智能体_查看,
        权限.监控_查看,
        权限.制品_读取,
    },
}

@dataclass
class 用户:
    """用户"""
    ID: str
    用户名: str
    邮箱: str
    角色列表: list[角色] = field(default_factory=list)
    是否激活: bool = True
    创建时间: datetime = field(default_factory=datetime.now)
    最后登录时间: datetime | None = None

@dataclass
class API密钥:
    """API密钥"""
    ID: str
    用户ID: str
    密钥哈希: str
    名称: str = ""
    创建时间: datetime = field(default_factory=datetime.now)
    过期时间: datetime | None = None
    是否激活: bool = True

class 认证服务:
    """
    认证服务

    处理用户认证和授权
    """

    def __init__(self):
        self._用户: dict[str, 用户] = {}
        self._API密钥: dict[str, API密钥] = {}
        self._密钥原文: dict[str, str] = {}  # 密钥ID -> 原文（仅用于展示一次）

    def 创建用户(
        self,
        用户名: str,
        邮箱: str,
        角色: 角色 = 角色.查看者
    ) -> 用户:
        """创建用户"""
        from uuid import uuid4
        用户ID = str(uuid4())

        用户对象 = 用户(
            ID=用户ID,
            用户名=用户名,
            邮箱=邮箱,
            角色列表=[角色]
        )

        self._用户[用户ID] = 用户对象
        logger.info(f"创建用户: {用户名} (ID: {用户ID}, 角色: {角色.value})")
        return 用户对象

    def 创建API密钥(
        self,
        用户ID: str,
        名称: str = "",
        有效天数: int = 90
    ) -> tuple[API密钥, str]:
        """
        创建API密钥

        Returns:
            (密钥对象, 密钥原文) - 密钥原文只返回一次
        """
        from uuid import uuid4

        用户 = self._用户.get(用户ID)
        if not 用户:
            raise ValueError(f"用户 {用户ID} 不存在")

        密钥ID = str(uuid4())
        密钥原文 = f"hb_{secrets.token_urlsafe(32)}"
        密钥哈希 = hashlib.sha256(密钥原文.encode()).hexdigest()

        API密钥对象 = API密钥(
            ID=密钥ID,
            用户ID=用户ID,
            密钥哈希=密钥哈希,
            名称=名称,
            过期时间=datetime.now() + timedelta(days=有效天数)
        )

        self._API密钥[密钥ID] = API密钥对象
        self._密钥原文[密钥ID] = 密钥原文

        logger.info(f"创建API密钥: {密钥ID} (用户: {用户ID})")
        return API密钥对象, 密钥原文

    def 验证密钥(self, 密钥原文: str) -> 用户 | None:
        """验证API密钥并返回用户"""
        密钥哈希 = hashlib.sha256(密钥原文.encode()).hexdigest()

        for 密钥 in self._API密钥.values():
            if 密钥.密钥哈希 == 密钥哈希:
                if not 密钥.是否激活:
                    return None
                if 密钥.过期时间 and 密钥.过期时间 < datetime.now():
                    return None

                用户 = self._用户.get(密钥.用户ID)
                if 用户 and 用户.是否激活:
                    用户.最后登录时间 = datetime.now()
                    return 用户

        return None

    def 检查权限(self, 用户: 用户, 权限: 权限) -> bool:
        """检查用户是否有指定权限"""
        for 角色 in 用户.角色列表:
            if 权限 in 角色权限映射.get(角色, set()):
                return True
        return False

    def 获取用户权限(self, 用户: 用户) -> set[权限]:
        """获取用户的所有权限"""
        所有权限 = set()
        for 角色 in 用户.角色列表:
            所有权限.update(角色权限映射.get(角色, set()))
        return 所有权限

    def 获取用户(self, 用户ID: str) -> 用户 | None:
        """获取用户"""
        return self._用户.get(用户ID)

    def 更新用户角色(self, 用户ID: str, 角色列表: list[角色]) -> bool:
        """更新用户角色"""
        用户 = self._用户.get(用户ID)
        if not 用户:
            return False
        用户.角色列表 = 角色列表
        logger.info(f"更新用户角色: {用户ID} -> {[r.value for r in 角色列表]}")
        return True

    def 禁用用户(self, 用户ID: str) -> bool:
        """禁用用户"""
        用户 = self._用户.get(用户ID)
        if not 用户:
            return False
        用户.是否激活 = False
        logger.info(f"禁用用户: {用户ID}")
        return True

    def 获取所有用户(self) -> list[用户]:
        """获取所有用户"""
        return list(self._用户.values())
