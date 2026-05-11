"""WebSocket路由"""
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from ..websocket import 管理器, 频道类型
from ...认证.RBAC import 认证服务

logger = logging.getLogger(__name__)
router = APIRouter()

_认证 = 认证服务()

@router.websocket("")
async def websocket端点(websocket: WebSocket):
    客户端ID = str(uuid.uuid4())
    api_key = websocket.query_params.get("api_key")

    if not api_key:
        await websocket.accept()
        await websocket.send_json({"类型": "error", "数据": {"消息": "认证失败：缺少API密钥"}})
        await websocket.close()
        return

    用户 = _认证.验证密钥(api_key)
    if not 用户:
        await websocket.accept()
        await websocket.send_json({"类型": "error", "数据": {"消息": "认证失败：缺少API密钥"}})
        await websocket.close()
        return

    成功 = await 管理器.连接(websocket, 客户端ID)
    if not 成功:
        return

    客户端 = 管理器._连接池.get(客户端ID)
    if 客户端:
        客户端.用户信息 = {"用户ID": 用户.ID, "用户名": 用户.用户名, "角色": [r.value for r in 用户.角色列表]}

    try:
        while True:
            原始消息 = await websocket.receive_text()
            await 管理器.处理消息(客户端ID, 原始消息)
    except WebSocketDisconnect:
        logger.info(f"客户端 {客户端ID} 主动断开连接")
    except Exception as e:
        logger.error(f"客户端 {客户端ID} 连接异常: {e}")
    finally:
        await 管理器.断开(客户端ID)
