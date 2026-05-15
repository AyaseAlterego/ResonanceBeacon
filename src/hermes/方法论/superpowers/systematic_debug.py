"""systematic-debugging 技能模板"""

systematic_debug模板 = """
你必须遵循 systematic-debugging 技能：

## Phase 1: 根因调查
- 仔细阅读错误信息
- 稳定复现问题
- 检查最近变更

## Phase 2: 模式分析
- 找到正常工作的类似代码
- 对比差异

## Phase 3: 假设与测试
- 提出单一假设
- 最小化测试

## Phase 4: 实施
- 先写失败测试
- 再修复根因

## 硬约束
- 不要在完成 Phase 1 之前提出任何修复
- 每个假设必须通过测试验证
"""
