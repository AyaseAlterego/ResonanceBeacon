"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import shutil
import logging

from .路由 import 流水线路由, 智能体路由, 审批路由, 配置路由, 健康路由, 插件市场路由, websocket路由, hermes路由, 项目路由, 对话路由, 制品路由, 看板路由
from .websocket import 管理器
from .存储 import 存储实例, 智能体记录

logger = logging.getLogger(__name__)


def 扫描本地智能体():
    """扫描本地可用的 AI 工具，注册为智能体"""
    # Claude Code
    claude路径 = shutil.which("claude")
    if claude路径:
        存储实例.智能体列表["claude_code"] = 智能体记录(
            ID="claude_code", 名称="Claude Code", 类别="ultrabrain",
            状态="idle", 是否在线=True
        )
        logger.info(f"检测到 Claude Code: {claude路径}")
    else:
        存储实例.智能体列表.pop("claude_code", None)

    # OpenCode
    opencode路径 = shutil.which("opencode")
    if opencode路径:
        存储实例.智能体列表["opencode"] = 智能体记录(
            ID="opencode", 名称="OpenCode", 类别="deep",
            状态="idle", 是否在线=True
        )
        logger.info(f"检测到 OpenCode: {opencode路径}")
    else:
        存储实例.智能体列表.pop("opencode", None)

    # Hermes 元智能体（始终存在）
    存储实例.智能体列表["hermes"] = 智能体记录(
        ID="hermes", 名称="Hermes Agent", 类别="ultrabrain",
        状态="idle", 是否在线=True
    )


@asynccontextmanager
async def 生命周期(app: FastAPI):
    """应用生命周期管理"""
    logger.info("起源信标服务启动中...")
    扫描本地智能体()
    logger.info(f"智能体扫描完成: {list(存储实例.智能体列表.keys())}")
    await 管理器.启动心跳检测()
    yield
    await 管理器.停止心跳检测()
    logger.info("起源信标服务关闭中...")

def 创建应用() -> FastAPI:
    """创建FastAPI应用"""
    应用 = FastAPI(
        title="起源信标 API",
        description="智能流水线开发系统 REST API",
        version="0.1.0",
        lifespan=生命周期
    )

    应用.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    应用.include_router(流水线路由.router, prefix="/流水线", tags=["流水线"])
    应用.include_router(智能体路由.router, prefix="/智能体", tags=["智能体"])
    应用.include_router(审批路由.router, prefix="/审批", tags=["审批"])
    应用.include_router(配置路由.router, prefix="/配置", tags=["配置"])
    应用.include_router(健康路由.router, tags=["健康检查"])
    应用.include_router(插件市场路由.router, prefix="/插件市场", tags=["插件市场"])
    应用.include_router(websocket路由.router, prefix="/ws", tags=["WebSocket"])
    应用.include_router(hermes路由.router, prefix="/智能体/hermes", tags=["Hermes"])
    应用.include_router(项目路由.router, prefix="/项目", tags=["项目"])
    应用.include_router(对话路由.router, prefix="/项目", tags=["对话"])
    应用.include_router(制品路由.router, prefix="/项目", tags=["制品"])
    应用.include_router(看板路由.router, tags=["看板"])

    return 应用

应用 = 创建应用()
