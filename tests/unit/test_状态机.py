"""状态机单元测试"""
import pytest
from src.hermes.编排器.状态机 import 流水线状态机

def test_状态机_设置状态():
    """测试设置状态"""
    状态机 = 流水线状态机()
    状态机.设置状态("流水线1", "pending")

    assert 状态机.获取状态("流水线1") == "pending"

def test_状态机_有效转换():
    """测试有效的状态转换"""
    状态机 = 流水线状态机()
    状态机.设置状态("流水线1", "pending")

    # 有效转换
    assert 状态机.验证转换("pending", "running") == True
    assert 状态机.验证转换("running", "completed") == True
    assert 状态机.验证转换("running", "failed") == True

    # 无效转换
    assert 状态机.验证转换("pending", "completed") == False
    assert 状态机.验证转换("completed", "running") == False

def test_状态机_状态转换():
    """测试状态转换"""
    状态机 = 流水线状态机()
    状态机.设置状态("流水线1", "pending")

    # 有效转换
    assert 状态机.转换状态("流水线1", "running") == True
    assert 状态机.获取状态("流水线1") == "running"

    # 无效转换
    assert 状态机.转换状态("流水线1", "pending") == False
    assert 状态机.获取状态("流水线1") == "running"

def test_状态机_终态检查():
    """测试终态检查"""
    状态机 = 流水线状态机()

    # pending不是终态
    状态机.设置状态("流水线1", "pending")
    assert 状态机.是终态("流水线1") == False

    # completed是终态
    状态机.设置状态("流水线2", "completed")
    assert 状态机.是终态("流水线2") == True

    # cancelled是终态
    状态机.设置状态("流水线3", "cancelled")
    assert 状态机.是终态("流水线3") == True

def test_状态机_获取允许的转换():
    """测试获取允许的转换"""
    状态机 = 流水线状态机()
    状态机.设置状态("流水线1", "pending")

    允许的转换 = 状态机.获取允许的转换("流水线1")

    assert "running" in 允许的转换
    assert "completed" not in 允许的转换
    assert "failed" not in 允许的转换

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
