"""测试上下文包"""
from src.hermes.智能体.基础 import 上下文包


def test_上下文包_默认值():
    包 = 上下文包()
    assert 包.流水线ID == ""
    assert 包.项目路径 == ""


def test_上下文包_设置项目路径():
    包 = 上下文包(项目路径="/tmp/my_project")
    assert 包.项目路径 == "/tmp/my_project"


def test_上下文包_完整初始化():
    包 = 上下文包(
        流水线ID="pl-1",
        阶段ID="sg-1",
        任务ID="tk-1",
        项目路径="/my/project"
    )
    assert 包.流水线ID == "pl-1"
    assert 包.项目路径 == "/my/project"
