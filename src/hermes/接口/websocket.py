"""WebSocket管理器"""
import asyncio
import json
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class 频道类型(str, Enum):
    流水线状态 = "pipeline_status"
    智能体状态 = "agent_status"
    审批通知 = "approval_request"
    系统事件 = "system_event"

class 消息类型(str, Enum):
    订阅 = "subscribe"
    退订 = "unsubscribe"
    流水线状态 = "pipeline_status"
    智能体状态 = "agent_status"
    审批请求 = "approval_request"
    系统事件 = "system_event"
    心跳 = "heartbeat"
    心跳回复 = "heartbeat_ack"
    错误 = "error"

@dataclass
class 客户端连接:
    连接: WebSocket
    订阅频道: set[频道类型] = field(default_factory=set)
    最后心跳时间: float = field(default_factory=time.time)
    客户端ID: str = ""
    用户信息: dict | None = None

class WebSocket管理器:
    def __init__(self, 心跳间隔: int = 30, 心跳超时: int = 60):
        self.心跳间隔 = 心跳间隔
        self.心跳超时 = 心跳超时
        self._连接池: dict[str, 客户端连接] = {}
        self._频道订阅: dict[频道类型, set[str]] = {
            频道: set() for 频道 in 频道类型
        }
        self._运行中 = False
        self._心跳任务: Optional[asyncio.Task] = None

    async def 连接(self, websocket: WebSocket, 客户端ID: str) -> bool:
        try:
            await websocket.accept()
            客户端 = 客户端连接(
                连接=websocket,
                客户端ID=客户端ID
            )
            self._连接池[客户端ID] = 客户端
            logger.info(f"WebSocket客户端已连接: {客户端ID}")
            return True
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False

    async def 断开(self, 客户端ID: str):
        客户端 = self._连接池.pop(客户端ID, None)
        if 客户端:
            for 频道 in 客户端.订阅频道:
                self._频道订阅[频道].discard(客户端ID)
            try:
                await 客户端.连接.close()
            except Exception:
                pass
            logger.info(f"WebSocket客户端已断开: {客户端ID}")

    async def 订阅频道(self, 客户端ID: str, 频道: 频道类型) -> bool:
        客户端 = self._连接池.get(客户端ID)
        if not 客户端:
            return False
        客户端.订阅频道.add(频道)
        self._频道订阅[频道].add(客户端ID)
        logger.info(f"客户端 {客户端ID} 订阅频道: {频道.value}")
        return True

    async def 退订频道(self, 客户端ID: str, 频道: 频道类型) -> bool:
        客户端 = self._连接池.get(客户端ID)
        if not 客户端:
            return False
        客户端.订阅频道.discard(频道)
        self._频道订阅[频道].discard(客户端ID)
        logger.info(f"客户端 {客户端ID} 退订频道: {频道.value}")
        return True

    async def 广播消息(self, 频道: 频道类型, 数据: dict):
        消息 = {
            "类型": 频道.value,
            "数据": 数据,
            "时间戳": time.time()
        }
        已断开 = []
        for 客户端ID in list(self._频道订阅[频道]):
            客户端 = self._连接池.get(客户端ID)
            if not 客户端:
                已断开.append(客户端ID)
                continue
            try:
                await 客户端.连接.send_json(消息)
            except Exception as e:
                logger.warning(f"发送消息到客户端 {客户端ID} 失败: {e}")
                已断开.append(客户端ID)
        for 客户端ID in 已断开:
            await self.断开(客户端ID)

    async def 发送消息(self, 客户端ID: str, 消息类型: 消息类型, 数据: dict = None):
        客户端 = self._连接池.get(客户端ID)
        if not 客户端:
            return
        消息 = {
            "类型": 消息类型.value,
            "数据": 数据 or {},
            "时间戳": time.time()
        }
        try:
            await 客户端.连接.send_json(消息)
        except Exception as e:
            logger.warning(f"发送消息到客户端 {客户端ID} 失败: {e}")
            await self.断开(客户端ID)

    async def 处理消息(self, 客户端ID: str, 原始消息: str):
        客户端 = self._连接池.get(客户端ID)
        if not 客户端:
            return
        try:
            消息 = json.loads(原始消息)
        except json.JSONDecodeError:
            await self.发送消息(客户端ID, 消息类型.错误, {"原因": "消息格式无效"})
            return

        消息类型值 = 消息.get("类型", "")
        频道值 = 消息.get("频道", "")

        if 消息类型值 == 消息类型.订阅.value:
            try:
                频道 = 频道类型(频道值)
                成功 = await self.订阅频道(客户端ID, 频道)
                if 成功:
                    await self.发送消息(客户端ID, 消息类型.订阅, {"频道": 频道值, "状态": "已订阅"})
                else:
                    await self.发送消息(客户端ID, 消息类型.错误, {"原因": f"订阅失败: {频道值}"})
            except ValueError:
                await self.发送消息(客户端ID, 消息类型.错误, {"原因": f"未知频道: {频道值}"})

        elif 消息类型值 == 消息类型.退订.value:
            try:
                频道 = 频道类型(频道值)
                成功 = await self.退订频道(客户端ID, 频道)
                if 成功:
                    await self.发送消息(客户端ID, 消息类型.退订, {"频道": 频道值, "状态": "已退订"})
                else:
                    await self.发送消息(客户端ID, 消息类型.错误, {"原因": f"退订失败: {频道值}"})
            except ValueError:
                await self.发送消息(客户端ID, 消息类型.错误, {"原因": f"未知频道: {频道值}"})

        elif 消息类型值 == 消息类型.心跳.value:
            客户端.最后心跳时间 = time.time()
            await self.发送消息(客户端ID, 消息类型.心跳回复, {"时间戳": time.time()})

        else:
            await self.发送消息(客户端ID, 消息类型.错误, {"原因": f"未知消息类型: {消息类型值}"})

    async def 启动心跳检测(self):
        self._运行中 = True
        self._心跳任务 = asyncio.create_task(self._心跳循环())
        logger.info("WebSocket心跳检测已启动")

    async def 停止心跳检测(self):
        self._运行中 = False
        if self._心跳任务:
            self._心跳任务.cancel()
            try:
                await self._心跳任务
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket心跳检测已停止")

    async def _心跳循环(self):
        while self._运行中:
            当前时间 = time.time()
            已断开 = []
            for 客户端ID, 客户端 in list(self._连接池.items()):
                if 当前时间 - 客户端.最后心跳时间 > self.心跳超时:
                    logger.warning(f"客户端 {客户端ID} 心跳超时")
                    已断开.append(客户端ID)
            for 客户端ID in 已断开:
                await self.断开(客户端ID)
            await asyncio.sleep(self.心跳间隔)

    def 获取连接数(self) -> int:
        return len(self._连接池)

    def 获取频道订阅数(self, 频道: 频道类型) -> int:
        return len(self._频道订阅.get(频道, set()))

管理器 = WebSocket管理器()
