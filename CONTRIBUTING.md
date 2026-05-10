# 贡献指南

感谢你对起源信标项目的贡献！本指南将帮助你了解如何为项目做出贡献。

## 目录

- [快速开始](#快速开始)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交更改](#提交更改)
- [Pull Request流程](#pull-request流程)
- [问题报告](#问题报告)
- [功能建议](#功能建议)

---

## 快速开始

### 1. Fork仓库

在GitHub上fork起源信标仓库到你的账户。

### 2. 克隆你的fork

```bash
git clone https://github.com/YOUR-USERNAME/ResonanceBeacon.git
cd ResonanceBeacon
```

### 3. 添加上游仓库

```bash
git remote add upstream https://github.com/AyaseAlterego/ResonanceBeacon.git
```

### 4. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

---

## 开发环境设置

### 前置要求

- Python 3.12+
- pip
- PostgreSQL 15+
- Redis 7+

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/YOUR-USERNAME/ResonanceBeacon.git
   cd ResonanceBeacon
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **安装开发依赖**
   ```bash
   pip install -e ".[dev]"
   ```

4. **启动数据库服务**
   ```bash
   docker-compose up -d postgres redis
   ```

5. **运行数据库迁移**
   ```bash
   alembic upgrade head
   ```

6. **配置环境变量**
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/hermes"
   export REDIS_URL="redis://localhost:6379/0"
   ```

---

## 代码规范

### 命名约定

本项目使用中文命名规范：

- **类名**: `类名`（如 `流水线引擎`、`智能体适配器`）
- **函数名**: `函数名()`（如 `执行任务()`、`获取配置()`）
- **变量名**: `变量名`（如 `任务ID`、`输出数据`）
- **常量**: `常量`（如 `默认超时时间`）

### 代码风格

- 使用 **Black** 进行代码格式化
- 使用 **Flake8** 进行代码检查
- 使用 **MyPy** 进行类型检查

```bash
# 格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

### 测试要求

- 所有新功能必须包含单元测试
- 测试文件放在 `tests/` 目录下
- 测试函数命名：`test_功能描述`
- 测试类命名：`Test类名`
- 使用 `pytest` 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/unit/test_钩子.py -v

# 运行性能测试
pytest tests/性能/ -v
```

### 文档要求

- 所有公共函数和类必须包含文档字符串
- 使用中文编写文档
- 文档字符串格式：Google风格

```python
def 执行任务(任务ID: str, 任务类型: str) -> 任务结果:
    """
    执行指定的任务

    Args:
        任务ID: 任务的唯一标识符
        任务类型: 任务的类型（如 "code_generation"）

    Returns:
        任务执行结果

    Raises:
        ValueError: 如果任务类型无效
    """
    pass
```

---

## 提交更改

### 提交消息格式

使用以下格式编写提交消息：

```
<类型>: <简短描述>

<详细描述（可选）>

相关Issue: #xxx
```

### 类型

- **feat**: 新功能
- **fix**: Bug修复
- **docs**: 文档更新
- **style**: 代码风格调整（不影响功能）
- **refactor**: 代码重构
- **test**: 添加或修改测试
- **chore**: 构建或工具链更改

### 示例

```bash
git commit -m "feat: 添加OpenCode适配器

实现了OpenCode CLI的智能体适配器，支持：
- 通过子进程执行OpenCode命令
- 流式输出支持
- 任务取消功能

相关Issue: #15"
```

---

## Pull Request流程

### 1. 确保代码质量

```bash
# 运行测试
pytest tests/ -v

# 格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

### 2. 推送你的分支

```bash
git push origin feature/your-feature-name
```

### 3. 创建Pull Request

- 访问你的fork仓库
- 点击 "Compare & pull request"
- 填写PR描述：
  - **标题**: 简短描述（参考提交消息格式）
  - **描述**: 详细说明更改内容、解决的问题、测试情况

### 4. 代码审查

- 等待维护者审查你的代码
- 根据反馈进行必要的修改
- 确保所有CI检查通过

### 5. 合并

审查通过后，维护者会将你的更改合并到主分支。

---

## 问题报告

### 报告Bug

使用GitHub Issues报告Bug，请包含：

1. **问题描述**: 简洁清晰地描述问题
2. **复现步骤**: 详细列出触发问题的步骤
3. **预期行为**: 说明应该发生什么
4. **实际行为**: 说明实际发生了什么
5. **环境信息**:
   - Python版本
   - 操作系统
   - 依赖版本

### 报告安全问题

如果发现安全问题，请**不要**公开报告。请通过邮件联系维护者：

security@your-project.com

---

## 功能建议

使用GitHub Issues提交功能建议，请包含：

1. **功能描述**: 详细说明建议的功能
2. **使用场景**: 描述这个功能会解决什么问题
3. **实现建议**（可选）: 如果你有实现想法，可以分享
4. **替代方案**（可选）: 你考虑过的其他方案

---

## 代码库结构

```
src/hermes/
├── 配置/                 # 配置系统
├── 模型/                 # ORM数据模型
├── 编排器/               # 流水线引擎
├── 智能体/               # 智能体适配器
├── 钩子/                 # 五层钩子系统
├── 后台/                 # 后台任务管理
├── 制品/                 # 制品存储
├── 人工/                 # 人工参与
├── 接口/                 # REST API
├── 命令行/               # CLI工具
├── 监控/                 # 监控指标
└── 认证/                 # 认证和权限
```

---

## 开发工作流

### 添加新智能体适配器

1. 在 `src/hermes/智能体/适配器/` 创建新文件
2. 继承 `智能体适配器` 基类
3. 实现所有必需方法
4. 在 `注册表.py` 中注册适配器
5. 添加单元测试

### 添加新钩子

1. 在 `src/hermes/钩子/` 的对应层目录创建新文件
2. 继承 `钩子` 基类
3. 实现 `执行()` 方法
4. 在对应的工厂中注册
5. 添加单元测试

### 修改配置系统

1. 更新 `src/hermes/配置/模式.py` 中的配置模式
2. 更新配置加载逻辑
3. 添加相应的测试
4. 更新文档

---

## 获取帮助

- **文档**: 查看 README.md 和项目文档
- **问题**: 在GitHub Issues中提问
- **讨论**: 在GitHub Discussions中参与讨论
- **邮件**: contact@your-project.com

---

## 许可证

贡献的代码将在MIT许可证下发布。通过提交PR，你同意将你的贡献在相同许可证下发布。

---

感谢你的贡献！🎉
