"""接口模块"""
from .应用 import 创建应用
from .websocket import 管理器, 频道类型, 消息类型

__all__ = ["创建应用", "管理器", "频道类型", "消息类型"]
