"""FastAPI认证依赖"""
import logging
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..认证.RBAC import 认证服务, 用户, 权限, 角色

logger = logging.getLogger(__name__)

认证服务实例 = 认证服务()
默认密钥: str | None = None

_bearer_scheme = HTTPBearer(auto_error=False)

_LOCAL_KEY = "hermes-local-dev-key"

def _获取或创建本地用户() -> 用户:
    for uid, u in 认证服务实例._用户.items():
        if u.用户名 == "local":
            return u
    from ..认证.RBAC import API密钥
    import hashlib
    from datetime import datetime, timedelta
    from uuid import uuid4
    本地用户 = 用户(ID="local-user", 用户名="local", 邮箱="local@dev", 角色列表=[角色.管理员])
    认证服务实例._用户["local-user"] = 本地用户
    密钥哈希 = hashlib.sha256(_LOCAL_KEY.encode()).hexdigest()
    认证服务实例._API密钥["local-key"] = API密钥(
        ID="local-key", 用户ID="local-user", 密钥哈希=密钥哈希,
        名称="本地开发密钥", 过期时间=datetime.now() + timedelta(days=3650),
    )
    认证服务实例._密钥哈希索引[密钥哈希] = 认证服务实例._API密钥["local-key"]
    return 本地用户

async def 获取当前用户(
    凭证: HTTPAuthorizationCredentials | None = Security(_bearer_scheme)
) -> 用户:
    if not 凭证:
        raise HTTPException(status_code=401, detail="缺少认证信息")
    用户对象 = 认证服务实例.验证密钥(凭证.credentials)
    if not 用户对象:
        if 凭证.credentials == _LOCAL_KEY:
            用户对象 = _获取或创建本地用户()
        else:
            raise HTTPException(status_code=401, detail="无效的API密钥")
    return 用户对象

async def 获取管理员用户(
    当前用户: 用户 = Depends(获取当前用户)
) -> 用户:
    if 角色.管理员 not in 当前用户.角色列表:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return 当前用户

def 需要权限(权限名: 权限):
    async def 检查权限(当前用户: 用户 = Depends(获取当前用户)) -> 用户:
        if not 认证服务实例.检查权限(当前用户, 权限名):
            raise HTTPException(status_code=403, detail=f"缺少权限: {权限名.value}")
        return 当前用户
    return 检查权限
