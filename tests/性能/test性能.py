"""性能测试"""
import pytest
import asyncio
import time
from src.hermes.编排器.调度器 import DAG调度器
from src.hermes.后台.并发 import 并发管理器
from src.hermes.智能体.健康检查器 import 健康检查器


@pytest.mark.performance
class Test DAG性能:
    """DAG调度器性能测试"""

    def test_大规模拓扑排序性能(self):
        """测试大规模DAG的拓扑排序性能"""
        调度器 = DAG调度器()

        # 创建1000个节点的DAG
        for i in range(1000):
            调度器.添加节点(f"node_{i}")

        # 添加线性依赖
        for i in range(999):
            调度器.添加边(f"node_{i}", f"node_{i+1}")

        开始时间 = time.perf_counter()
        结果 = 调度器.拓扑排序()
        执行时间 = time.perf_counter() - 开始时间

        assert len(结果) == 1000
        assert 执行时间 < 1.0  # 应该在1秒内完成

    def test_大规模并发分组性能(self):
        """测试大规模DAG的并发分组性能"""
        调度器 = DAG调度器()

        # 创建1000个无依赖的节点
        for i in range(1000):
            调度器.添加节点(f"node_{i}")

        开始时间 = time.perf_counter()
        分组 = 调度器.获取并发组()
        执行时间 = time.perf_counter() - 开始时间

        assert len(分组) == 1  # 所有节点都应该在同一组
        assert len(分组[0]) == 1000
        assert 执行时间 < 0.5  # 应该在0.5秒内完成


@pytest.mark.performance
class Test 并发管理器性能:
    """并发管理器性能测试"""

    @pytest.mark.asyncio
    async def test_并发许可获取性能(self):
        """测试并发许可获取性能"""
        管理器 = 并发管理器(每智能体最大并发=100)

        开始时间 = time.perf_counter()

        # 并发获取100个许可
        任务列表 = []
        for i in range(100):
            任务列表.append(管理器.获取许可("agent_1"))

        结果 = await asyncio.gather(*任务列表)
        执行时间 = time.perf_counter() - 开始时间

        assert all(结果)
        assert 执行时间 < 0.1  # 应该在0.1秒内完成


@pytest.mark.performance
class Test 健康检查器性能:
    """健康检查器性能测试"""

    def test_负载统计计算性能(self):
        """测试负载统计计算性能"""
        检查器 = 健康检查器()

        # 记录大量任务
        开始时间 = time.perf_counter()
        for i in range(1000):
            检查器.记录任务开始(f"task_{i}", f"agent_{i % 10}")
            检查器.记录任务完成(f"task_{i}", f"agent_{i % 10}", True)
        执行时间 = time.perf_counter() - 开始时间

        assert 执行时间 < 1.0  # 应该在1秒内完成

        # 计算负载统计
        开始时间 = time.perf_counter()
        统计列表 = 检查器.获取所有负载统计()
        计算时间 = time.perf_counter() - 开始时间

        assert len(统计列表) == 10  # 10个不同的agent
        assert 计算时间 < 0.1  # 应该在0.1秒内完成
