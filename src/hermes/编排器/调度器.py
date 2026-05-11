"""有向无环图调度器"""
from typing import Any
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class 依赖循环检测异常(Exception):
    """依赖循环检测异常"""
    pass

class DAG调度器:
    """
    有向无环图（DAG）调度器

    负责任务依赖关系的拓扑排序、并发分组和执行调度
    """

    def __init__(self):
        self._图: dict[str, set[str]] = defaultdict(set)
        self._入度: dict[str, int] = defaultdict(int)
        self._节点数据: dict[str, dict[str, Any]] = {}

    def 添加节点(self, 节点ID: str, 数据: dict[str, Any] | None = None):
        """添加节点"""
        if 节点ID not in self._图:
            self._图[节点ID] = set()
        if 节点ID not in self._入度:
            self._入度[节点ID] = 0
        if 数据:
            self._节点数据[节点ID] = 数据

    def 添加边(self, 来源: str, 目标: str):
        """
        添加有向边（来源 -> 目标）

        表示目标依赖于来源，来源必须先完成
        """
        self.添加节点(来源)
        self.添加节点(目标)

        if 目标 not in self._图[来源]:
            self._图[来源].add(目标)
            self._入度[目标] += 1

    def 从定义构建(self, 节点列表: list[dict[str, Any]], 依赖键: str = "depends_on"):
        """
        从流水线定义构建DAG

        Args:
            节点列表: 节点定义列表，每个节点必须有 "id" 字段
            依赖键: 依赖关系的字段名（默认 "depends_on"）
        """
        self._图.clear()
        self._入度.clear()
        self._节点数据.clear()

        for 节点 in 节点列表:
            节点ID = 节点.get("id")
            if not 节点ID:
                raise ValueError(f"节点缺少 id 字段: {节点}")

            self.添加节点(节点ID, 节点)

            依赖IDs = 节点.get(依赖键, [])
            for 依赖ID in 依赖IDs:
                self.添加边(依赖ID, 节点ID)

    def 检测循环(self) -> bool:
        """
        检测是否存在循环

        Returns:
            True 如果存在循环
        """
        入度副本 = dict(self._入度)
        队列 = deque([节点 for 节点, 度 in 入度副本.items() if 度 == 0])
        已访问 = 0

        while 队列:
            节点 = 队列.popleft()
            已访问 += 1
            for 邻居 in self._图[节点]:
                入度副本[邻居] -= 1
                if 入度副本[邻居] == 0:
                    队列.append(邻居)

        return 已访问 != len(self._入度)

    def 拓扑排序(self) -> list[str]:
        """
        拓扑排序，返回节点的执行顺序

        Returns:
            按拓扑排序的节点ID列表

        Raises:
            依赖循环检测异常: 如果检测到循环
        """
        if self.检测循环():
            raise 依赖循环检测异常("检测到依赖循环，无法进行拓扑排序")

        入度副本 = dict(self._入度)
        队列 = deque([节点 for 节点, 度 in 入度副本.items() if 度 == 0])
        结果 = []

        while 队列:
            节点 = 队列.popleft()
            结果.append(节点)

            for 邻居 in self._图[节点]:
                入度副本[邻居] -= 1
                if 入度副本[邻居] == 0:
                    队列.append(邻居)

        return 结果

    def 获取并发组(self) -> list[list[str]]:
        """
        获取并发执行分组

        返回可以并行执行的任务分组列表，每组内的任务互不依赖

        Returns:
            分组列表，每组是可以并行执行的任务ID列表
        """
        if self.检测循环():
            raise 依赖循环检测异常("检测到依赖循环，无法生成并发组")

        入度副本 = dict(self._入度)
        已完成 = set()
        分组列表 = []

        while len(已完成) < len(self._入度):
            当前组 = []

            for 节点, 度 in 入度副本.items():
                if 节点 not in 已完成 and 度 == 0:
                    当前组.append(节点)

            if not 当前组:
                break

            分组列表.append(当前组)
            已完成.update(当前组)

            for 节点 in 当前组:
                for 邻居 in self._图[节点]:
                    入度副本[邻居] -= 1

        return 分组列表

    def 获取依赖链(self, 节点ID: str) -> list[str]:
        """获取节点的所有依赖（递归）"""
        if 节点ID not in self._节点数据:
            return []

        链 = []
        节点 = self._节点数据[节点ID]
        依赖IDs = 节点.get("depends_on", [])

        for 依赖ID in 依赖IDs:
            链.append(依赖ID)
            链.extend(self.获取依赖链(依赖ID))

        return list(dict.fromkeys(链))  # 去重保持顺序

    def 获取下游(self, 节点ID: str) -> list[str]:
        """获取依赖于该节点的所有下游节点"""
        return list(self._图.get(节点ID, set()))

    def 获取节点数据(self, 节点ID: str) -> dict[str, Any] | None:
        """获取节点数据"""
        return self._节点数据.get(节点ID)

    def 获取节点数量(self) -> int:
        """获取节点总数"""
        return len(self._入度)

    def 清空(self):
        """清空DAG"""
        self._图.clear()
        self._入度.clear()
        self._节点数据.clear()

    def __repr__(self) -> str:
        return f"<DAG调度器: {self.获取节点数量()} 个节点>"
