"""命令行命令模块"""
from .项目 import app as 项目命令
from .流水线 import app as 流水线命令
from .智能体 import app as 智能体命令
from .配置 import app as 配置命令
from .健康 import app as 健康命令

__all__ = [
    "项目命令",
    "流水线命令",
    "智能体命令",
    "配置命令",
    "健康命令"
]
