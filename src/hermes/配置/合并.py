"""安全深度合并工具，防止原型污染"""
from typing import Any
import logging

logger = logging.getLogger(__name__)

# 危险的键列表
DANGEROUS_KEYS = frozenset(["__proto__", "constructor", "prototype"])

def 安全深度合并(
    基础: dict[str, Any],
    覆盖: dict[str, Any],
    深度: int = 0,
    最大深度: int = 50
) -> dict[str, Any]:
    """
    安全的深度合并，阻止原型污染

    特性：
    1. 递归合并嵌套字典
    2. 阻止 __proto__, constructor, prototype 键
    3. 支持深度限制防止无限递归
    4. 列表使用集合并集策略（去重）
    """
    if 深度 > 最大深度:
        raise ValueError(f"合并深度超过最大限制 ({最大深度})，可能存在循环引用")

    结果 = 基础.copy()

    for 键, 值 in 覆盖.items():
        # 阻止原型污染
        if 键 in DANGEROUS_KEYS:
            raise ValueError(f"阻止潜在危险的键: {键}")

        # 递归合并嵌套字典
        if 键 in 结果 and isinstance(结果[键], dict) and isinstance(值, dict):
            结果[键] = 安全深度合并(结果[键], 值, 深度 + 1, 最大深度)

        # 集合并集策略处理列表（去重）
        elif 键 in 结果 and isinstance(结果[键], list) and isinstance(值, list):
            结果[键] = list(set(结果[键] + 值))

        # 其他情况直接覆盖
        else:
            结果[键] = 值

    return 结果

def 安全深度合并多层(
    层级列表: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    多层级合并（从最不具体到最具体）

    用法：安全深度合并多层([默认值, 用户配置, 项目配置])
    """
    if not 层级列表:
        raise ValueError("层级列表不能为空")

    结果 = 层级列表[0].copy()

    for 层级 in 层级列表[1:]:
        结果 = 安全深度合并(结果, 层级)

    return 结果

def 检查原型污染(数据: dict[str, Any]) -> list[str]:
    """
    检查字典中是否存在潜在的原型污染键

    返回所有危险的键路径列表
    """
    危险键路径 = []

    def _递归检查(字典: dict[str, Any], 路径: str = ""):
        for 键 in 字典:
            当前路径 = f"{路径}.{键}" if 路径 else 键

            if 键 in DANGEROUS_KEYS:
                危险键路径.append(当前路径)

            if isinstance(字典[键], dict):
                _递归检查(字典[键], 当前路径)

    _递归检查(数据)
    return 危险键路径
