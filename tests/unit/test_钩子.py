"""钩子系统单元测试"""
import pytest
from src.hermes.钩子.组合器 import 钩子组合器
from src.hermes.钩子.基础 import 钩子, 钩子层级, 钩子事件, 钩子上下文, 安全创建钩子
from src.hermes.钩子.会话 import 会话钩子工厂
from src.hermes.钩子.工具守护 import 工具守护钩子工厂
from src.hermes.钩子.转换 import 转换钩子工厂
from src.hermes.钩子.继续 import 继续钩子工厂
from src.hermes.钩子.技能 import 技能钩子工厂


class Test钩子基础:
    """钩子基础测试"""

    def test_钩子创建(self):
        """测试钩子创建"""
        def 回调():
            pass

        钩子实例 = 钩子(
            名称="测试钩子",
            层级=钩子层级.会话,
            事件=钩子事件.流水线已启动,
            回调=回调,
            优先级=5,
            描述="测试钩子"
        )

        assert 钩子实例.名称 == "测试钩子"
        assert 钩子实例.层级 == 钩子层级.会话
        assert 钩子实例.事件 == 钩子事件.流水线已启动
        assert 钩子实例.优先级 == 5

    def test_安全创建钩子成功(self):
        """测试安全创建钩子成功"""
        def 工厂(上下文):
            return 钩子(
                名称="测试钩子",
                层级=钩子层级.会话,
                事件=钩子事件.流水线已启动,
                回调=lambda: None,
                优先级=5
            )

        上下文 = 钩子上下文(流水线={}, 元数据={})
        结果 = 安全创建钩子("测试钩子", 工厂, 上下文)

        assert 结果 is not None
        assert 结果.名称 == "测试钩子"

    def test_安全创建钩子失败(self):
        """测试安全创建钩子失败"""
        def 工厂(上下文):
            raise ValueError("创建失败")

        上下文 = 钩子上下文(流水线={}, 元数据={})
        结果 = 安全创建钩子("测试钩子", 工厂, 上下文)

        assert 结果 is None


class Test钩子工厂:
    """钩子工厂测试"""

    def test_会话钩子工厂创建(self):
        """测试会话钩子工厂创建"""
        工厂 = 会话钩子工厂()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        钩子列表 = 工厂.创建钩子(上下文)

        assert len(钩子列表) == 7
        for 钩子实例 in 钩子列表:
            assert 钩子实例.层级 == 钩子层级.会话

    def test_工具守护钩子工厂创建(self):
        """测试工具守护钩子工厂创建"""
        工厂 = 工具守护钩子工厂()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        钩子列表 = 工厂.创建钩子(上下文)

        assert len(钩子列表) == 4
        for 钩子实例 in 钩子列表:
            assert 钩子实例.层级 == 钩子层级.工具守护

    def test_转换钩子工厂创建(self):
        """测试转换钩子工厂创建"""
        工厂 = 转换钩子工厂()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        钩子列表 = 工厂.创建钩子(上下文)

        assert len(钩子列表) == 3
        for 钩子实例 in 钩子列表:
            assert 钩子实例.层级 == 钩子层级.转换

    def test_继续钩子工厂创建(self):
        """测试继续钩子工厂创建"""
        工厂 = 继续钩子工厂()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        钩子列表 = 工厂.创建钩子(上下文)

        assert len(钩子列表) == 3
        for 钩子实例 in 钩子列表:
            assert 钩子实例.层级 == 钩子层级.继续

    def test_技能钩子工厂创建(self):
        """测试技能钩子工厂创建"""
        工厂 = 技能钩子工厂()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        钩子列表 = 工厂.创建钩子(上下文)

        assert len(钩子列表) == 2
        for 钩子实例 in 钩子列表:
            assert 钩子实例.层级 == 钩子层级.技能


class Test钩子组合器:
    """钩子组合器测试"""

    def test_组合所有层级(self):
        """测试组合所有层级"""
        组合器 = 钩子组合器()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        结果 = 组合器.组合(上下文)

        assert 钩子层级.会话 in 结果
        assert 钩子层级.工具守护 in 结果
        assert 钩子层级.转换 in 结果
        assert 钩子层级.继续 in 结果
        assert 钩子层级.技能 in 结果

    def test_获取钩子数量(self):
        """测试获取钩子数量"""
        组合器 = 钩子组合器()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        结果 = 组合器.组合(上下文)
        数量 = 组合器.获取钩子数量(结果)

        assert 数量 == 19  # 7 + 4 + 3 + 3 + 2

    def test_触发钩子(self):
        """测试触发钩子"""
        组合器 = 钩子组合器()
        上下文 = 钩子上下文(流水线={}, 元数据={})

        钩子字典 = 组合器.组合(上下文)

        # 触发流水线已启动事件
        try:
            组合器.触发钩子(钩子字典, 钩子事件.流水线已启动, {})
        except Exception as e:
            pytest.fail(f"触发钩子失败: {e}")


class Test钩子层级:
    """钩子层级测试"""

    def test_钩子层级值(self):
        """测试钩子层级值"""
        assert 钩子层级.会话.value == "session"
        assert 钩子层级.工具守护.value == "tool_guard"
        assert 钩子层级.转换.value == "transform"
        assert 钩子层级.继续.value == "continuation"
        assert 钩子层级.技能.value == "skill"


class Test钩子事件:
    """钩子事件测试"""

    def test_钩子事件值(self):
        """测试钩子事件值"""
        assert 钩子事件.流水线已启动.value == "pipeline_started"
        assert 钩子事件.流水线已完成.value == "pipeline_completed"
        assert 钩子事件.阶段已开始.value == "stage_started"
        assert 钩子事件.任务已开始.value == "task_started"
