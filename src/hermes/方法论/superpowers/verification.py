"""verification-before-completion 技能模板"""

verification模板 = """
你必须遵循 verification-before-completion 技能：

## 流程
1. 运行所有测试，确认全部通过
2. 检查代码是否符合 spec
3. 检查是否有 TODO/FIXME 残留
4. 检查是否有调试代码未移除
5. 运行 lint/typecheck
6. 确认构建通过

## 硬约束
- 在任何声称"完成"之前，必须完成以上所有检查
- 如果任何检查失败，不能标记为完成
- 记录所有检查结果
"""
