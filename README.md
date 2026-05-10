# 起源信标 (ResonanceBeacon)

**智能流水线开发系统**

Hermes Agent作为元智能体，调度Claude Code、OpenCode、Codex等AI工具进行流水线式开发。

---

## 核心特性

### 🎯 基于类别的智能体路由
- 通过类别描述任务需求，系统自动选择最佳智能体
- 支持8个类别：超级大脑、深度、快速、视觉工程、专家、探索、顾问、工具

### 🔒 安全的配置系统
- 多层级配置：项目级 > 用户级 > 默认值
- 防止原型污染的安全深度合并
- 支持JSONC格式（带注释的JSON）

### ⚙️ 五层钩子系统
- 会话层：生命周期事件
- 工具守护层：工具执行守护
- 转换层：消息/上下文变换
- 继续层：循环管理，重试
- 技能层：技能生命周期

### 🛡️ 强大的容错性
- 安全创建模式：一个组件失败不会崩溃整个系统
- 熔断器模式：自动检测和恢复故障
- 并发管理器：防止过载

### 🔄 完整的流水线支持
- 需求分析
- 设计文档
- 确认审批
- 开发实现
- 测试验证
- 审查评估
- 交付部署

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/AyaseAlterego/ResonanceBeacon.git
cd ResonanceBeacon

# 安装依赖
pip install -e .
```

### 启动服务

```bash
# 启动PostgreSQL和Redis
docker-compose up -d

# 运行数据库迁移
alembic upgrade head

# 启动命令行工具
hermes --help
```

### 运行第一个流水线

```bash
hermes 流水线运行 流水线定义.json --input "构建一个REST API"
```

---

## 架构设计

```
src/hermes/
├── 配置/                 # 多层级配置系统
│   ├── 模式.py          # Pydantic配置模式
│   ├── 合并.py          # 安全深度合并
│   └── 配置加载器.py    # 配置加载器
├── 模型/                 # 数据模型
│   ├── 项目.py
│   ├── 流水线.py
│   ├── 阶段.py
│   ├── 任务.py
│   ├── 制品.py
│   └── 决策.py
├── 编排器/               # 流水线引擎
│   ├── 引擎.py          # 流水线引擎
│   └── 状态机.py        # 状态机
├── 智能体/               # 智能体层
│   ├── 基础.py          # 智能体适配器接口
│   ├── 注册表.py        # 智能体注册表
│   ├── 类别.py          # 基于类别的路由
│   └── 适配器/          # 具体适配器
├── 钩子/                 # 五层钩子系统
│   ├── 基础.py          # 钩子定义
│   ├── 组合器.py        # 钩子组合器
│   └── 会话/            # 会话层钩子
├── 后台/                 # 后台任务管理器
│   ├── 管理器.py        # 后台任务管理器
│   ├── 并发.py          # 并发管理器
│   └── 熔断器.py        # 熔断器
├── 制品/                 # 制品存储
├── 人工/                 # 人工参与
├── 接口/                 # REST API
├── 命令行/               # 命令行工具
└── 模板/                 # 流水线模板
```

---

## 设计模式

### 1. 基于类别的智能体路由
不是直接指定使用哪个智能体，而是通过**类别**来描述任务需求，系统自动路由到最佳智能体。

### 2. 工厂+依赖注入模式
每个组件通过工厂函数创建，支持依赖注入用于测试。

### 3. 安全创建模式
包装所有工厂创建，确保一个组件失败不会崩溃整个系统。

### 4. 多层级配置系统
配置优先级：项目级 > 用户级 > 默认值，支持closest-wins策略。

### 5. 五层钩子系统
将系统生命周期钩子组织为5个层级，便于管理和扩展。

### 6. 后台任务管理器
借鉴oh-my-openagent的BackgroundManager，实现强大的任务调度和容错。

---

## 配置示例

```jsonc
{
  // 项目配置
  "项目名称": "我的项目",
  "环境": "development",

  // 智能体配置
  "智能体": {
    "claude_code": {
      "模型": "claude-3-5-sonnet-20241022",
      "最大令牌数": 4096,
      "温度": 0.3
    }
  },

  // 类别配置
  "类别": {
    "ultrabrain": {
      "描述": "架构级，高难度逻辑",
      "智能体优先级": ["claude_code"]
    }
  },

  // 流水线配置
  "流水线默认值": {
    "最大重试次数": 3,
    "任务超时": 600
  }
}
```

---

## 流水线定义示例

```json
{
  "name": "REST API开发",
  "stages": [
    {
      "id": "requirements",
      "name": "需求分析",
      "type": "sequential",
      "tasks": [
        {
          "id": "analyze_requirements",
          "name": "分析需求",
          "type": "requirements_engineering",
          "category": "exploration"
        }
      ]
    },
    {
      "id": "design",
      "name": "架构设计",
      "type": "sequential",
      "tasks": [
        {
          "id": "architecture_design",
          "name": "设计架构",
          "type": "architecture_design",
          "category": "ultrabrain"
        }
      ]
    },
    {
      "id": "development",
      "name": "开发实现",
      "type": "parallel",
      "tasks": [
        {
          "id": "backend",
          "name": "后端开发",
          "type": "code_generation",
          "category": "deep"
        },
        {
          "id": "frontend",
          "name": "前端开发",
          "type": "code_generation",
          "category": "visual-engineering"
        }
      ]
    }
  ]
}
```

---

## 测试

```bash
# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行所有测试
pytest tests/ -v
```

---

## 项目状态

### ✅ 阶段1: 基础搭建 - 已完成
- [x] 项目搭建
- [x] Docker Compose配置（PostgreSQL + Redis）
- [x] 数据模型（ORM with SQLAlchemy 2.0）
- [x] 多层级配置系统（项目级 > 用户级 > 默认值）
- [x] 安全深度合并（防原型污染）
- [x] 智能体基础接口（抽象基类）
- [x] 类别路由器（8个智能体类别）
- [x] 五层钩子系统（会话、工具守护、转换、继续、技能）
- [x] 后台任务管理器（并发控制、熔断器）
- [x] 流水线引擎（DAG调度、状态机）
- [x] 命令行工具（完整CLI界面）

### ✅ 阶段2: 多智能体和并发 - 已完成
- [x] 智能体注册表和健康检查
- [x] Claude Code适配器
- [x] OpenCode适配器
- [x] Codex适配器
- [x] 任务队列（异步任务处理）
- [x] 并发阶段支持（并行任务调度）
- [x] 上下文管理器（令牌预算管理）

### ✅ 阶段3: 人工参与和接口 - 已完成
- [x] 人工界面服务（审批系统）
- [x] REST API（FastAPI实现）
- [x] 配置接口（动态配置管理）

### ✅ 阶段4: 质量和韧性 - 已完成
- [x] 测试框架（pytest + asyncio）
- [x] 熔断器完善（自动故障恢复）
- [x] 制品存储（内容寻址，SHA-256去重）
- [x] 监控系统（指标收集、健康监控）
- [x] 集成测试（25个测试全部通过）

### ✅ 阶段5: 生产加固 - 已完成
- [x] 认证和权限（RBAC，4个角色，17个权限）
- [x] API密钥管理
- [x] 插件系统（动态加载、类型接口）
- [x] 流水线模板
- [x] CLI命令完善（5个命令组）
- [x] 提示词模板系统（动态生成）

### 📋 阶段6: Web前端和文档 - 待完成
- [ ] React + TailwindCSS仪表板（可选）
- [ ] 文档完善
- [ ] 部署指南
- [ ] 贡献指南

---

## 参考项目

本项目的设计模式借鉴了 [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) 的优秀设计：

- 基于类别的智能体路由
- 工厂+依赖注入模式
- 安全创建模式
- 多层级配置系统
- 五层钩子系统
- 后台任务管理器
- 熔断器模式

---

## 许可证

MIT License

---

## 贡献

欢迎贡献！请查看 CONTRIBUTING.md 了解详情。
