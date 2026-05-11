"""WebSocket客户端示例"""
import asyncio
import json
import websockets

WS地址 = "ws://localhost:8000/ws"

async def 运行客户端():
    async with websockets.connect(WS地址) as 连接:
        print(f"已连接到 {WS地址}")

        订阅消息 = json.dumps({
            "类型": "subscribe",
            "频道": "pipeline_status"
        })
        await 连接.send(订阅消息)
        print("已订阅: pipeline_status")

        订阅消息 = json.dumps({
            "类型": "subscribe",
            "频道": "agent_status"
        })
        await 连接.send(订阅消息)
        print("已订阅: agent_status")

        订阅消息 = json.dumps({
            "类型": "subscribe",
            "频道": "approval_request"
        })
        await 连接.send(订阅消息)
        print("已订阅: approval_request")

        订阅消息 = json.dumps({
            "类型": "subscribe",
            "频道": "system_event"
        })
        await 连接.send(订阅消息)
        print("已订阅: system_event")

        async def 心跳循环():
            while True:
                await asyncio.sleep(20)
                心跳消息 = json.dumps({"类型": "heartbeat"})
                await 连接.send(心跳消息)
                print("已发送心跳")

        心跳任务 = asyncio.create_task(心跳循环())

        try:
            async for 原始消息 in 连接:
                消息 = json.loads(原始消息)
                消息类型 = 消息.get("类型", "")
                数据 = 消息.get("数据", {})
                时间戳 = 消息.get("时间戳", "")

                if 消息类型 == "heartbeat_ack":
                    print(f"[心跳回复] {时间戳}")
                elif 消息类型 == "subscribe":
                    print(f"[订阅确认] {数据}")
                elif 消息类型 == "unsubscribe":
                    print(f"[退订确认] {数据}")
                elif 消息类型 == "pipeline_status":
                    print(f"[流水线状态] 流水线ID={数据.get('流水线ID')} 状态={数据.get('状态')}")
                elif 消息类型 == "agent_status":
                    print(f"[智能体状态] 智能体ID={数据.get('智能体ID')} 状态={数据.get('状态')}")
                elif 消息类型 == "approval_request":
                    print(f"[审批请求] 审批ID={数据.get('审批ID')} 流水线ID={数据.get('流水线ID')}")
                elif 消息类型 == "system_event":
                    print(f"[系统事件] {数据}")
                elif 消息类型 == "error":
                    print(f"[错误] {数据}")
                else:
                    print(f"[未知消息] {消息}")
        finally:
            心跳任务.cancel()

if __name__ == "__main__":
    asyncio.run(运行客户端())
