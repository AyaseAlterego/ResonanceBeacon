"""测试内存存储"""
from src.hermes.接口.存储 import 内存存储


def test_创建和获取流水线():
    s = 内存存储()
    p = s.创建流水线("测试流水线", "描述")
    assert p.ID is not None
    assert p.名称 == "测试流水线"
    获取的 = s.获取流水线(p.ID)
    assert 获取的 is not None
    assert 获取的.名称 == "测试流水线"


def test_获取不存在流水线():
    s = 内存存储()
    assert s.获取流水线("不存在的ID") is None


def test_获取所有流水线():
    s = 内存存储()
    s.创建流水线("A")
    s.创建流水线("B")
    assert len(s.获取所有流水线()) == 2


def test_空存储_无智能体():
    s = 内存存储()
    assert len(s.获取所有智能体()) == 0


def test_查找不存在的智能体():
    s = 内存存储()
    assert s.查找智能体("nonexistent") is None


def test_审批待处理():
    s = 内存存储()
    a1 = s.添加审批("pl-1", "审批1")
    a2 = s.添加审批("pl-2", "审批2")
    a2.状态 = "approved"
    待处理 = s.获取待审批()
    assert len(待处理) == 1
    assert 待处理[0].ID == a1.ID
