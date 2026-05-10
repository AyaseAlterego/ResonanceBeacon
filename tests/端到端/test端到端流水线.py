"""端到端流水线测试"""
import pytest
from src.hermes.编排器.引擎 import 流水线引擎
from src.hermes.智能体 import 智能体注册表, 类别路由器
from src.hermes.智能体.基础 import 智能体类别
from src.hermes.后台 import 后台任务管理器
from tests.mock.mock智能体 import 模拟智能体


@pytest.mark.end_to_end
class Test端到端流水线执行:
    """端到端流水线执行测试"""

    @pytest.mark.asyncio
    async def test_单阶段单任务执行(self):
        """测试单阶段单任务端到端执行"""
        # 设置智能体
        mock智能体 = 模拟智能体(延迟秒=0.01)
        注册表 = 智能体注册表()
        注册表.注册智能体(mock智能体)

        路由器 = 类别路由器()
        路由器.设置注册表(注册表)
        for 类别 in 智能体类别:
            路由器.注册类别路由(类别, ["mock_agent"])

        后台管理器 = 后台任务管理器()

        # 创建引擎
        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )

        # 定义流水线
        流水线定义 = {
            "id": "e2e-single",
            "name": "端到端单任务测试",
            "stages": [
                {
                    "id": "stage1",
                    "name": "阶段1",
                    "type": "sequential",
                    "tasks": [
                        {
                            "id": "task1",
                            "name": "测试任务",
                            "type": "general",
                            "category": "utility",
                            "input": {"key": "value"}
                        }
                    ]
                }
            ]
        }

        # 执行流水线
        结果 = await 引擎.运行流水线(流水线定义, "端到端测试输入")

        # 验证结果
        assert 结果.状态 == "completed"
        assert 结果.流水线ID == "e2e-single"
        assert 结果.阶段数 == 1
        assert 结果.完成阶段数 == 1

    @pytest.mark.asyncio
    async def test_多阶段串行执行(self):
        """测试多阶段串行端到端执行"""
        mock智能体 = 模拟智能体(延迟秒=0.01)
        注册表 = 智能体注册表()
        注册表.注册智能体(mock智能体)

        路由器 = 类别路由器()
        路由器.设置注册表(注册表)
        for 类别 in 智能体类别:
            路由器.注册类别路由(类别, ["mock_agent"])

        后台管理器 = 后台任务管理器()

        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )

        流水线定义 = {
            "id": "e2e-multi-stage",
            "name": "端到端多阶段测试",
            "stages": [
                {
                    "id": "stage1",
                    "name": "需求分析",
                    "type": "sequential",
                    "tasks": [
                        {
                            "id": "task1",
                            "name": "分析需求",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                },
                {
                    "id": "stage2",
                    "name": "设计",
                    "type": "sequential",
                    "tasks": [
                        {
                            "id": "task2",
                            "name": "系统设计",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                },
                {
                    "id": "stage3",
                    "name": "实现",
                    "type": "sequential",
                    "tasks": [
                        {
                            "id": "task3",
                            "name": "代码实现",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                }
            ]
        }

        结果 = await 引擎.运行流水线(流水线定义, "多阶段端到端测试")

        assert 结果.状态 == "completed"
        assert 结果.阶段数 == 3
        assert 结果.完成阶段数 == 3

    @pytest.mark.asyncio
    async def test_并发任务执行(self):
        """测试并发任务端到端执行"""
        mock智能体 = 模拟智能体(延迟秒=0.01)
        注册表 = 智能体注册表()
        注册表.注册智能体(mock智能体)

        路由器 = 类别路由器()
        路由器.设置注册表(注册表)
        for 类别 in 智能体类别:
            路由器.注册类别路由(类别, ["mock_agent"])

        后台管理器 = 后台任务管理器()

        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )

        流水线定义 = {
            "id": "e2e-parallel",
            "name": "端到端并发测试",
            "stages": [
                {
                    "id": "parallel-stage",
                    "name": "并发阶段",
                    "type": "parallel",
                    "tasks": [
                        {
                            "id": "task1",
                            "name": "并行任务1",
                            "type": "general",
                            "category": "utility"
                        },
                        {
                            "id": "task2",
                            "name": "并行任务2",
                            "type": "general",
                            "category": "utility"
                        },
                        {
                            "id": "task3",
                            "name": "并行任务3",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                }
            ]
        }

        结果 = await 引擎.运行流水线(流水线定义, "并发端到端测试")

        assert 结果.状态 == "completed"
        assert 结果.阶段数 == 1
        assert 结果.完成阶段数 == 1

    @pytest.mark.asyncio
    async def test_混合串行并发执行(self):
        """测试混合串行和并发端到端执行"""
        mock智能体 = 模拟智能体(延迟秒=0.01)
        注册表 = 智能体注册表()
        注册表.注册智能体(mock智能体)

        路由器 = 类别路由器()
        路由器.设置注册表(注册表)
        for 类别 in 智能体类别:
            路由器.注册类别路由(类别, ["mock_agent"])

        后台管理器 = 后台任务管理器()

        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )

        流水线定义 = {
            "id": "e2e-mixed",
            "name": "端到端混合测试",
            "stages": [
                {
                    "id": "stage1",
                    "name": "串行阶段",
                    "type": "sequential",
                    "tasks": [
                        {
                            "id": "task1",
                            "name": "串行任务",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                },
                {
                    "id": "stage2",
                    "name": "并发阶段",
                    "type": "parallel",
                    "tasks": [
                        {
                            "id": "task2",
                            "name": "并行任务1",
                            "type": "general",
                            "category": "utility"
                        },
                        {
                            "id": "task3",
                            "name": "并行任务2",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                }
            ]
        }

        结果 = await 引擎.运行流水线(流水线定义, "混合端到端测试")

        assert 结果.状态 == "completed"
        assert 结果.阶段数 == 2
        assert 结果.完成阶段数 == 2


@pytest.mark.end_to_end
class Test端到端错误处理:
    """端到端错误处理测试"""

    @pytest.mark.asyncio
    async def test_无智能体失败处理(self):
        """测试无可用智能体时的失败处理"""
        注册表 = 智能体注册表()  # 空注册表

        路由器 = 类别路由器()
        路由器.设置注册表(注册表)
        for 类别 in 智能体类别:
            路由器.注册类别路由(类别, [])  # 空路由

        后台管理器 = 后台任务管理器()

        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )

        流水线定义 = {
            "id": "e2e-no-agent",
            "name": "端到端无智能体测试",
            "stages": [
                {
                    "id": "stage1",
                    "name": "阶段1",
                    "type": "sequential",
                    "tasks": [
                        {
                            "id": "task1",
                            "name": "任务1",
                            "type": "general",
                            "category": "utility"
                        }
                    ]
                }
            ]
        }

        结果 = await 引擎.运行流水线(流水线定义, "无智能体测试")

        assert 结果.状态 == "failed"
        assert 结果.错误 is not None
