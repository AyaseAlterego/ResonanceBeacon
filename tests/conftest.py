"""测试配置和共享fixtures"""
import pytest
import asyncio
from pathlib import Path

from src.hermes.智能体 import 智能体注册表, 类别路由器
from src.hermes.智能体.基础 import 智能体类别
from src.hermes.后台 import 后台任务管理器
from src.hermes.编排器.引擎 import 流水线引擎
from src.hermes.编排器.调度器 import DAG调度器
from src.hermes.编排器.状态机 import 流水线状态机
from src.hermes.配置 import 配置加载器
from tests.mock.mock智能体 import 模拟智能体


@pytest.fixture
def mock智能体():
    """创建默认模拟智能体"""
    return 模拟智能体(延迟秒=0.01)


@pytest.fixture
def 快速mock智能体():
    """创建快速模拟智能体（无延迟）"""
    return 模拟智能体(延迟秒=0.0)


@pytest.fixture
def 慢速mock智能体():
    """创建慢速模拟智能体"""
    return 模拟智能体(延迟秒=0.5)


@pytest.fixture
def 不可靠mock智能体():
    """创建不可靠模拟智能体（50%失败率）"""
    return 模拟智能体(延迟秒=0.01, 失败率=0.5)


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


@pytest.fixture
def 流水线引擎实例(注册表, 类别路由, 后台管理器):
    """创建流水线引擎实例"""
    return 流水线引擎(
        智能体注册表=注册表,
        类别路由器=类别路由,
        后台管理器=后台管理器
    )


@pytest.fixture
def DAG调度器实例():
    """创建DAG调度器实例"""
    return DAG调度器()


@pytest.fixture
def 状态机实例():
    """创建流水线状态机实例"""
    return 流水线状态机()


@pytest.fixture
def 简单流水线定义():
    """创建简单流水线定义"""
    return {
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
                        "category": "utility"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def 多阶段流水线定义():
    """创建多阶段流水线定义"""
    return {
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


@pytest.fixture
def 并发流水线定义():
    """创建并发流水线定义"""
    return {
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


@pytest.fixture
def 测试项目目录(tmp_path):
    """创建临时测试项目目录"""
    项目目录 = tmp_path / "test_project"
    项目目录.mkdir()
    配置目录 = 项目目录 / ".hermes"
    配置目录.mkdir()
    return 项目目录


@pytest.fixture
def 配置加载器实例():
    """创建配置加载器实例"""
    return 配置加载器()


# pytest配置
def pytest_configure(config):
    """配置pytest"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
