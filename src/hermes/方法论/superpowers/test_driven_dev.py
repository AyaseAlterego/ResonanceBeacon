"""test-driven-development 技能模板"""

test_driven_dev模板 = """
你必须遵循 test-driven-development 技能：

## 流程
1. RED: 先写一个失败测试
2. 验证测试失败（MANDATORY，不可跳过）
3. GREEN: 写最小代码使测试通过
4. 验证测试通过
5. REFACTOR: 清理代码
6. 所有测试仍然通过

## 硬约束
- 如果你在写测试之前写了实现代码，删除它，从头开始
- 不要跳过 RED 阶段。如果没有看到测试失败，你不知道测试的是否正确
- 每个任务完成后必须运行所有测试
"""
