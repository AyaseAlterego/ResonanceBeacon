"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import shutil
import logging
import asyncio

from .路由 import 流水线路由, 智能体路由, 审批路由, 配置路由, 健康路由, 插件市场路由, websocket路由, hermes路由, 项目路由, 对话路由, 制品路由, 看板路由, 自主循环路由
from .websocket import 管理器
from .存储 import 存储实例, 智能体记录

logger = logging.getLogger(__name__)

# 全局自主循环引擎实例
自主循环引擎实例 = None


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


def 初始化自主循环引擎():
    """初始化自主循环引擎"""
    global 自主循环引擎实例

    from ..编排层 import 自主循环引擎, 自主循环配置, CTO智能体, PM智能体, Dev智能体, Security智能体, QA智能体, Ops智能体
    from ..编排层.看板 import Kanban状态机
    from ..智能体 import 智能体注册表, 类别路由器
    from ..后台 import 后台任务管理器

    # 创建自主循环配置
    配置 = 自主循环配置(
        扫描间隔秒=3600,
        最大并发任务=3,
        自动审批=False,
    )

    # 创建自主循环引擎
    自主循环引擎实例 = 自主循环引擎(配置)

    # 注册6个智能体
    自主循环引擎实例.注册智能体(
        CTO智能体=CTO智能体(),
        PM智能体=PM智能体(),
        Dev智能体=Dev智能体(),
        Security智能体=Security智能体(),
        QA智能体=QA智能体(),
        Ops智能体=Ops智能体(),
    )

    # 注册依赖
    看板 = Kanban状态机()
    自主循环引擎实例.注册依赖(
        看板=看板,
        执行层接口=None,  # 后续注入
        存储=存储实例,
    )

    # 设置审批回调
    def 审批回调(卡片ID: str, 消息: str):
        logger.info(f"自主循环审批通知: 卡片 {卡片ID} - {消息[:100]}...")
        # 这里可以通过 WebSocket 推送给前端

    自主循环引擎实例.设置审批回调(审批回调)

    logger.info("自主循环引擎初始化完成")
    return 自主循环引擎实例


@asynccontextmanager
async def 生命周期(app: FastAPI):
    """应用生命周期管理"""
    logger.info("起源信标服务启动中...")
    扫描本地智能体()
    logger.info(f"智能体扫描完成: {list(存储实例.智能体列表.keys())}")

    # 初始化自主循环引擎
    global 自主循环引擎实例
    自主循环引擎实例 = 初始化自主循环引擎()
    自主循环路由.设置自主循环引擎实例(自主循环引擎实例)
    审批路由.设置自主循环引擎实例(自主循环引擎实例)

    # 启动自主循环（默认启动）
    asyncio.create_task(自主循环引擎实例.启动())
    logger.info("自主循环引擎已启动")

    await 管理器.启动心跳检测()
    yield

    # 关闭时停止自主循环
    if 自主循环引擎实例:
        await 自主循环引擎实例.停止()
        logger.info("自主循环引擎已停止")

    await 管理器.停止心跳检测()
    logger.info("起源信标服务关闭中...")


def 创建应用() -> FastAPI:
    """创建FastAPI应用"""
    应用 = FastAPI(
        title="起源信标 API",
        description="智能流水线开发系统 REST API (Oh My Hermes 编排层)",
        version="0.2.0",
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
    应用.include_router(自主循环路由.router, tags=["自主循环"])

    return 应用

应用 = 创建应用()
