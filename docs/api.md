# API文档

起源信标提供RESTful API接口，用于管理和监控流水线执行。

## 目录

- [认证](#认证)
- [基础端点](#基础端点)
- [项目管理](#项目管理)
- [流水线管理](#流水线管理)
- [智能体管理](#智能体管理)
- [配置管理](#配置管理)
- [监控指标](#监控指标)
- [错误处理](#错误处理)

---

## 认证

所有API请求需要在请求头中包含API密钥：

```http
Authorization: Bearer YOUR_API_KEY
```

或使用查询参数：

```
?api_key=YOUR_API_KEY
```

### 获取API密钥

```bash
# 通过CLI创建API密钥
hermes 认证 创建密钥 --name "my-api-key" --role developer
```

### 权限层级

- **admin**: 完全访问权限
- **owner**: 项目所有者权限
- **developer**: 开发者权限（可运行流水线、查看状态）
- **viewer**: 只读权限（只能查看状态）

---

## 基础端点

### 健康检查

检查系统健康状况。

```http
GET /api/v1/health
```

**响应**:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "agents": "healthy"
  }
}
```

### 版本信息

获取系统版本信息。

```http
GET /api/v1/version
```

**响应**:

```json
{
  "version": "0.1.0",
  "python_version": "3.12.0",
  "environment": "production"
}
```

---

## 项目管理

### 创建项目

创建新项目。

```http
POST /api/v1/projects
```

**请求体**:

```json
{
  "名称": "我的项目",
  "描述": "项目描述",
  "配置": {
    "环境": "development",
    "智能体": {
      "claude_code": {
        "模型": "claude-3-5-sonnet-20241022"
      }
    }
  }
}
```

**响应**:

```json
{
  "ID": "uuid",
  "名称": "我的项目",
  "创建时间": "2024-01-15T10:30:00Z",
  "状态": "active"
}
```

### 获取项目列表

获取所有项目。

```http
GET /api/v1/projects
```

**查询参数**:

- `limit`: 返回数量限制（默认：20）
- `offset`: 偏移量（默认：0）
- `status`: 按状态过滤

**响应**:

```json
{
  "items": [
    {
      "ID": "uuid",
      "名称": "项目1",
      "状态": "active",
      "创建时间": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 10,
  "limit": 20,
  "offset": 0
}
```

### 获取项目详情

获取指定项目的详细信息。

```http
GET /api/v1/projects/{项目ID}
```

**响应**:

```json
{
  "ID": "uuid",
  "名称": "我的项目",
  "描述": "项目描述",
  "配置": {},
  "创建时间": "2024-01-15T10:30:00Z",
  "更新时间": "2024-01-15T10:30:00Z",
  "状态": "active",
  "流水线数量": 5,
  "智能体数量": 3
}
```

---

## 流水线管理

### 创建流水线

创建新的流水线定义。

```http
POST /api/v1/pipelines
```

**请求体**:

```json
{
  "名称": "REST API开发流水线",
  "项目ID": "uuid",
  "定义": {
    "name": "REST API开发",
    "stages": [
      {
        "id": "requirements",
        "name": "需求分析",
        "type": "sequential",
        "tasks": [
          {
            "id": "analyze",
            "name": "分析需求",
            "type": "requirements_engineering",
            "category": "exploration"
          }
        ]
      }
    ]
  }
}
```

### 运行流水线

启动流水线执行。

```http
POST /api/v1/pipelines/{流水线ID}/run
```

**请求体**:

```json
{
  "输入": {
    "需求": "构建一个REST API",
    "技术栈": "FastAPI"
  },
  "配置覆盖": {
    "最大重试次数": 5
  }
}
```

**响应**:

```json
{
  "执行ID": "uuid",
  "状态": "running",
  "开始时间": "2024-01-15T10:30:00Z"
}
```

### 获取流水线状态

获取流水线执行状态。

```http
GET /api/v1/pipelines/{流水线ID}/status
```

**响应**:

```json
{
  "流水线ID": "uuid",
  "执行ID": "uuid",
  "状态": "running",
  "当前阶段": "development",
  "进度": {
    "总任务数": 10,
    "完成任务数": 5,
    "失败任务数": 1,
    "百分比": 50.0
  },
  "阶段": [
    {
      "ID": "requirements",
      "名称": "需求分析",
      "状态": "completed",
      "开始时间": "2024-01-15T10:30:00Z",
      "结束时间": "2024-01-15T10:35:00Z"
    }
  ],
  "制品": [
    {
      "ID": "uuid",
      "类型": "code",
      "哈希": "abc123...",
      "大小": 1024
    }
  ]
}
```

### 获取流水线日志

获取流水线执行日志。

```http
GET /api/v1/pipelines/{流水线ID}/logs
```

**查询参数**:

- `level`: 日志级别（info、warning、error）
- `limit`: 返回数量限制（默认：100）
- `offset`: 偏移量

### 取消流水线

取消正在运行的流水线。

```http
POST /api/v1/pipelines/{流水线ID}/cancel
```

**请求体**:

```json
{
  "原因": "需求变更"
}
```

### 暂停/恢复流水线

暂停或恢复流水线执行。

```http
POST /api/v1/pipelines/{流水线ID}/pause
POST /api/v1/pipelines/{流水线ID}/resume
```

---

## 智能体管理

### 获取智能体列表

获取所有注册的智能体。

```http
GET /api/v1/agents
```

**响应**:

```json
{
  "智能体": [
    {
      "ID": "claude_code",
      "名称": "Claude Code",
      "类别": "ultrabrain",
      "能力": [
        {
          "名称": "code_generation",
          "语言": ["python", "javascript"],
          "上下文窗口": 200000
        }
      ],
      "状态": "healthy",
      "负载": {
        "当前任务数": 2,
        "最大并发数": 5,
        "利用率": 0.4
      }
    }
  ]
}
```

### 获取智能体详情

获取指定智能体的详细信息。

```http
GET /api/v1/agents/{智能体ID}
```

### 执行智能体健康检查

触发智能体健康检查。

```http
POST /api/v1/agents/{智能体ID}/health-check
```

**响应**:

```json
{
  "智能体ID": "claude_code",
  "状态": "healthy",
  "检查时间": "2024-01-15T10:30:00Z",
  "响应时间": 150,
  "错误": null
}
```

### 获取智能体负载

获取智能体负载统计。

```http
GET /api/v1/agents/{智能体ID}/load
```

**响应**:

```json
{
  "智能体ID": "claude_code",
  "当前任务数": 2,
  "最大并发数": 5,
  "平均响应时间": 5000,
  "成功率": 0.95,
  "总任务数": 100,
  "失败任务数": 5
}
```

---

## 配置管理

### 获取配置

获取当前合并后的配置。

```http
GET /api/v1/config
```

**查询参数**:

- `层级`: 配置层级（project、user、system、default）

### 更新配置

更新配置值。

```http
PUT /api/v1/config
```

**请求体**:

```json
{
  "路径": "智能体.claude_code.温度",
  "值": 0.5,
  "层级": "project"
}
```

### 验证配置

验证配置有效性。

```http
POST /api/v1/config/validate
```

**请求体**:

```json
{
  "配置": {
    "环境": "production",
    "智能体": {}
  }
}
```

**响应**:

```json
{
  "有效": true,
  "错误": null,
  "警告": []
}
```

---

## 监控指标

### 获取监控指标

获取系统监控指标。

```http
GET /api/v1/metrics
```

**查询参数**:

- `指标`: 特定指标名称
- `开始时间`: 开始时间（ISO 8601格式）
- `结束时间`: 结束时间（ISO 8601格式）

**响应**:

```json
{
  "流水线执行数": {
    "总执行数": 100,
    "成功数": 90,
    "失败数": 10,
    "成功率": 0.9
  },
  "任务执行": {
    "总任务数": 500,
    "平均执行时间": 5000,
    "P95执行时间": 10000
  },
  "令牌使用": {
    "总输入令牌": 1000000,
    "总输出令牌": 500000,
    "平均成本": 0.15
  }
}
```

### 获取指标历史

获取指标历史数据。

```http
GET /api/v1/metrics/{指标名}/history
```

**查询参数**:

- `粒度`: 数据粒度（minute、hour、day）
- `开始时间`: 开始时间
- `结束时间`: 结束时间

---

## 人工审批

### 获取待审批列表

获取需要人工审批的任务。

```http
GET /api/v1/approvals
```

**查询参数**:

- `状态`: 审批状态（pending、approved、rejected）
- `流水线ID`: 按流水线过滤

**响应**:

```json
{
  "待审批": [
    {
      "决策ID": "uuid",
      "流水线ID": "uuid",
      "阶段ID": "uuid",
      "类型": "approval",
      "状态": "pending",
      "请求者": "流水线引擎",
      "上下文": {
        "制品ID": "uuid",
        "制品内容": "..."
      },
      "创建时间": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 批准任务

批准待审批的任务。

```http
POST /api/v1/approvals/{决策ID}/approve
```

**请求体**:

```json
{
  "决策者": "user@example.com",
  "反馈": "代码质量良好，批准通过"
}
```

### 拒绝任务

拒绝待审批的任务。

```http
POST /api/v1/approvals/{决策ID}/reject
```

**请求体**:

```json
{
  "决策者": "user@example.com",
  "反馈": "代码存在安全问题，需要修改",
  "要求修改": true
}
```

---

## 错误处理

所有错误响应遵循以下格式：

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "无效的输入数据",
    "details": {
      "字段": "名称",
      "原因": "不能为空"
    }
  }
}
```

### 常见错误码

- `400 Bad Request`: 请求格式错误
- `401 Unauthorized`: 认证失败
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突
- `422 Unprocessable Entity`: 输入验证失败
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务不可用

### 错误示例

```json
{
  "error": {
    "code": "PIPELINE_NOT_FOUND",
    "message": "流水线不存在",
    "details": {
      "流水线ID": "invalid-uuid"
    }
  }
}
```

---

## 速率限制

API实施速率限制以防止滥用：

- **管理员**: 1000 requests/minute
- **所有者**: 500 requests/minute
- **开发者**: 200 requests/minute
- **查看者**: 100 requests/minute

超出限制将返回 `429 Too Many Requests` 错误。

---

## SDK和客户端

### Python SDK

```python
from hermes import HermesClient

client = HermesClient(api_key="your-api-key")

# 获取流水线状态
status = client.pipelines.get_status("pipeline-id")

# 运行流水线
execution = client.pipelines.run("pipeline-id", input={"需求": "..."})
```

### cURL示例

```bash
# 获取所有流水线
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/pipelines

# 运行流水线
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"输入": {"需求": "构建API"}}' \
  http://localhost:8000/api/v1/pipelines/uuid/run
```

---

## WebSocket实时更新

连接WebSocket以获取实时状态更新：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?api_key=YOUR_API_KEY');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('流水线更新:', data);
};

// 订阅特定流水线
ws.send(JSON.stringify({
  action: 'subscribe',
  pipeline_id: 'uuid'
}));
```

### 事件类型

- `pipeline.started`: 流水线开始执行
- `pipeline.completed`: 流水线执行完成
- `pipeline.failed`: 流水线执行失败
- `stage.started`: 阶段开始执行
- `stage.completed`: 阶段执行完成
- `task.started`: 任务开始执行
- `task.completed`: 任务执行完成
- `task.failed`: 任务执行失败
- `approval.requested`: 请求人工审批
- `approval.decided`: 审批决定

---

## 示例工作流

### 完整的流水线执行流程

```bash
# 1. 创建项目
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"名称": "我的项目"}' \
  http://localhost:8000/api/v1/projects

# 2. 创建流水线
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"名称": "API开发", "项目ID": "uuid", "定义": {...}}' \
  http://localhost:8000/api/v1/pipelines

# 3. 运行流水线
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"输入": {"需求": "构建REST API"}}' \
  http://localhost:8000/api/v1/pipelines/uuid/run

# 4. 监控状态
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/pipelines/uuid/status

# 5. 处理审批（如果需要）
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"决策者": "user@example.com", "反馈": "批准"}' \
  http://localhost:8000/api/v1/approvals/uuid/approve
```

---

## 更多资源

- [README.md](../README.md) - 项目概述和快速开始
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南
- [DEPLOYMENT.md](./deployment.md) - 部署指南
- [examples/](../examples/) - 示例代码和流水线定义
