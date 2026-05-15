"""kanban-task 技能模板"""

kanban_task模板 = """
你必须遵循 kanban-task 技能：

## 流程
1. 创建 Kanban 卡片（Backlog 列）
2. 更新卡片状态（Backlog → In Progress → Review → Done）
3. 记录状态转换历史
4. 在卡片上附加制品和 PR 信息

## 状态转换规则
- Backlog → In Progress: 开始开发
- In Progress → Review: 开发完成，等待审查
- Review → Done: 审查通过，合并部署
- Review → In Progress: 审查不通过，需要修改
- 任何状态 → Cancelled: 任务取消

## 卡片字段
- ID, 标题, 描述
- 状态, 优先级, 负责人
- 关联任务, 关联制品
- 创建时间, 更新时间, 完成时间
"""
