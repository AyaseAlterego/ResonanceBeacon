"""implement 技能模板"""

implement模板 = """
你必须遵循 implement 技能：

## 流程
1. 阅读产品简报和设计文档
2. 选择合适的执行引擎（Hermes/Claude Code/Codex）
3. 执行开发，遵循 TDD
4. 创建 PR
5. 等待审查

## 引擎选择
- 单文件修复 → Codex
- 多文件开发 → Claude Code / OpenCode
- 简单脚本 → Hermes 直接执行

## 硬约束
- 不提交密钥或敏感信息
- 每个变更都要有测试
- 代码必须通过 lint 和 typecheck
"""
