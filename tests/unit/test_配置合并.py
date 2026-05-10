"""配置合并单元测试"""
import pytest
from src.hermes.配置.合并 import 安全深度合并, 安全深度合并多层, 检查原型污染

def test_安全深度合并_基本合并():
    """测试基本的深度合并"""
    基础 = {"a": 1, "b": {"c": 2}}
    覆盖 = {"b": {"d": 3}, "e": 4}

    结果 = 安全深度合并(基础, 覆盖)

    assert 结果["a"] == 1
    assert 结果["b"]["c"] == 2
    assert 结果["b"]["d"] == 3
    assert 结果["e"] == 4

def test_安全深度合并_原型污染防护():
    """测试原型污染防护"""
    基础 = {"a": 1}
    覆盖 = {"__proto__": {"恶意": "数据"}}

    with pytest.raises(ValueError) as excinfo:
        安全深度合并(基础, 覆盖)

    assert "阻止潜在危险的键" in str(excinfo.value)

def test_安全深度合并_列表合并():
    """测试列表的集合并集合并"""
    基础 = {"列表": [1, 2, 3]}
    覆盖 = {"列表": [3, 4, 5]}

    结果 = 安全深度合并(基础, 覆盖)

    # 列表应该被去重
    assert set(结果["列表"]) == {1, 2, 3, 4, 5}

def test_安全深度合并_深度限制():
    """测试深度限制"""
    # 创建一个很深的字典（正确的方式）
    深字典 = {}
    当前 = 深字典
    for i in range(60):
        当前["level"] = {}
        当前 = 当前["level"]

    覆盖 = {"level": {}}
    当前覆盖 = 覆盖
    for i in range(60):
        当前覆盖["level"] = {}
        当前覆盖 = 当前覆盖["level"]

    with pytest.raises(ValueError) as excinfo:
        安全深度合并(深字典, 覆盖)

    assert "合并深度超过最大限制" in str(excinfo.value)

def test_安全深度合并多层_多层合并():
    """测试多层合并"""
    层级1 = {"a": 1, "b": {"c": 1}}
    层级2 = {"b": {"d": 2}, "e": 3}
    层级3 = {"b": {"c": 10}, "f": 4}

    结果 = 安全深度合并多层([层级1, 层级2, 层级3])

    assert 结果["a"] == 1
    assert 结果["b"]["c"] == 10  # 层级3覆盖
    assert 结果["b"]["d"] == 2
    assert 结果["e"] == 3
    assert 结果["f"] == 4

def test_检查原型污染_检测危险键():
    """测试原型污染检测"""
    数据 = {
        "a": 1,
        "__proto__": {"恶意": "数据"},
        "b": {"constructor": "危险"}
    }

    危险键 = 检查原型污染(数据)

    assert "__proto__" in 危险键
    assert "b.constructor" in 危险键
    assert "a" not in 危险键

def test_检查原型污染_安全数据():
    """测试安全数据"""
    数据 = {
        "a": 1,
        "b": {"c": 2},
        "d": [1, 2, 3]
    }

    危险键 = 检查原型污染(数据)

    assert len(危险键) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
