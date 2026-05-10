"""流水线集成测试"""
import pytest
import asyncio
from src.hermes.编排器.引擎 import 流水线引擎, 流水线结果
from src.hermes.编排器.状态机 import 流水线状态机
from src.hermes.编排器.调度器 import DAG调度器
from src.hermes.智能体 import 智能体注册表, 类别路由器
from src.hermes.智能体.基础 import 智能体类别
from src.hermes.后台 import 后台任务管理器
from tests.mock import 模拟智能体

@pytest.fixture
def mock智能体():
    """创建模拟智能体"""
    return 模拟智能体(延迟秒=0.01)

@pytest.fixture
def 注册表(mock智能体):
    """创建智能体注册表"""
    表 = 智能体注册表()
    表.注册智能体(mock智能体)
    return 表

@pytest.fixture
def 类别路由(注册表):
    """创建类别路由器"""
    路由器 = 类别路由器()
    路由器.设置注册表(注册表)
    # 注册mock_agent到所有类别路由中
    for 类别 in 智能体类别:
        路由器.注册类别路由(类别, ["mock_agent"])
    return 路由器

@pytest.fixture
def 后台管理器():
    """创建后台管理器"""
    return 后台任务管理器(每智能体最大并发=5, 任务超时=30)

def test_状态机_基本转换():
    """测试状态机基本转换"""
    机 = 流水线状态机()

    机.设置状态("p1", "pending")
    assert 机.获取状态("p1") == "pending"

    成功 = 机.转换状态("p1", "running")
    assert 成功 is True
    assert 机.获取状态("p1") == "running"

    成功 = 机.转换状态("p1", "completed")
    assert 成功 is True
    assert 机.获取状态("p1") == "completed"

def test_状态机_无效转换():
    """测试无效状态转换"""
    机 = 流水线状态机()
    机.设置状态("p1", "pending")

    # pending -> completed 无效
    成功 = 机.转换状态("p1", "completed")
    assert 成功 is False
    assert 机.获取状态("p1") == "pending"

def test_状态机_终态():
    """测试终态检测"""
    机 = 流水线状态机()

    机.设置状态("p1", "completed")
    assert 机.是终态("p1") is True

    机.设置状态("p2", "running")
    assert 机.是终态("p2") is False

def test_DAG调度器_拓扑排序():
    """测试DAG调度器拓扑排序"""
    调度器 = DAG调度器()

    调度器.添加节点("A")
    调度器.添加节点("B")
    调度器.添加节点("C")
    调度器.添加边("A", "B")
    调度器.添加边("B", "C")

    排序结果 = 调度器.拓扑排序()
    assert 排序结果.index("A") < 排序结果.index("B")
    assert 排序结果.index("B") < 排序结果.index("C")

def test_DAG调度器_循环检测():
    """测试DAG循环检测"""
    调度器 = DAG调度器()

    调度器.添加节点("A")
    调度器.添加节点("B")
    调度器.添加边("A", "B")
    调度器.添加边("B", "A")

    assert 调度器.检测循环() is True

def test_DAG调度器_并发分组():
    """测试DAG并发分组"""
    调度器 = DAG调度器()

    # A -> C, B -> C (A和B可以并发)
    调度器.添加节点("A")
    调度器.添加节点("B")
    调度器.添加节点("C")
    调度器.添加边("A", "C")
    调度器.添加边("B", "C")

    分组 = 调度器.获取并发组()

    # 应该有2组: [{A, B}, {C}]
    assert len(分组) == 2
    assert set(分组[0]) == {"A", "B"}
    assert 分组[1] == ["C"]

def test_智能体注册表(mock智能体):
    """测试智能体注册表"""
    表 = 智能体注册表()
    表.注册智能体(mock智能体)

    assert 表.获取智能体数量() == 1
    获取的 = 表.获取智能体("mock_agent")
    assert 获取的 is not None
    assert 获取的.智能体ID == "mock_agent"

def test_类别路由器(类别路由, mock智能体):
    """测试类别路由器"""
    from src.hermes.智能体.基础 import 智能体类别, 任务需求

    # 将mock_agent注册到路由表中
    类别路由.注册类别路由(智能体类别.工具, ["mock_agent"])

    需求 = 任务需求(能力列表=["general"], 预估令牌数=1000)
    选择的智能体 = 类别路由.选择智能体(智能体类别.工具, 需求)

    assert 选择的智能体 is not None
    assert 选择的智能体.智能体ID == "mock_agent"

@pytest.mark.asyncio
async def test_流水线引擎简单执行(注册表, 类别路由, 后台管理器, mock智能体):
    """测试简单流水线执行"""
    引擎 = 流水线引擎(
        智能体注册表=注册表,
        类别路由器=类别路由,
        后台管理器=后台管理器
    )

    流水线定义 = {
        "id": "test-pipeline",
        "name": "测试流水线",
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
                        "category": "utility",
                        "input": {"key": "value"}
                    }
                ]
            }
        ]
    }

    结果 = await 引擎.运行流水线(流水线定义, "测试输入")

    assert 结果.状态 == "completed"
    assert 结果.流水线ID == "test-pipeline"
    assert 结果.阶段数 == 1

@pytest.mark.asyncio
async def test_流水线引擎多阶段执行(注册表, 类别路由, 后台管理器):
    """测试多阶段流水线执行"""
    引擎 = 流水线引擎(
        智能体注册表=注册表,
        类别路由器=类别路由,
        后台管理器=后台管理器
    )

    流水线定义 = {
        "id": "multi-stage",
        "name": "多阶段流水线",
        "stages": [
            {
                "id": "requirements",
                "name": "需求分析",
                "type": "sequential",
                "tasks": [{"id": "req-1", "name": "分析需求", "category": "utility"}]
            },
            {
                "id": "design",
                "name": "设计",
                "type": "sequential",
                "tasks": [{"id": "des-1", "name": "系统设计", "category": "utility"}]
            }
        ]
    }

    结果 = await 引擎.运行流水线(流水线定义, "多阶段测试")

    assert 结果.状态 == "completed"
    assert 结果.阶段数 == 2
    assert 结果.完成阶段数 == 2

@pytest.mark.asyncio
async def test_流水线引擎并发阶段(注册表, 类别路由, 后台管理器):
    """测试并发阶段执行"""
    引擎 = 流水线引擎(
        智能体注册表=注册表,
        类别路由器=类别路由,
        后台管理器=后台管理器
    )

    流水线定义 = {
        "id": "parallel",
        "name": "并发流水线",
        "stages": [
            {
                "id": "parallel-stage",
                "name": "并发阶段",
                "type": "parallel",
                "tasks": [
                    {"id": "p-1", "name": "并行任务1", "category": "utility"},
                    {"id": "p-2", "name": "并行任务2", "category": "utility"},
                    {"id": "p-3", "name": "并行任务3", "category": "utility"}
                ]
            }
        ]
    }

    结果 = await 引擎.运行流水线(流水线定义, "并发测试")

    assert 结果.状态 == "completed"
    assert 结果.阶段数 == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
