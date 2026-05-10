# 部署指南

本指南介绍如何在生产环境中部署起源信标系统。

## 目录

- [部署选项](#部署选项)
- [系统要求](#系统要求)
- [Docker Compose部署](#docker-compose部署)
- [Kubernetes部署](#kubernetes部署)
- [环境变量配置](#环境变量配置)
- [数据库设置](#数据库设置)
- [Redis设置](#redis设置)
- [反向代理配置](#反向代理配置)
- [SSL/TLS证书](#ssltls证书)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [性能调优](#性能调优)
- [故障排除](#故障排除)

---

## 部署选项

### 选项1: Docker Compose（推荐）

适合中小型部署，简单快速。

### 选项2: Kubernetes

适合大规模、高可用部署。

### 选项3: 裸机/VM部署

适合有特殊需求的环境。

---

## 系统要求

### 最小配置（开发/测试环境）

- **CPU**: 2核
- **内存**: 4GB RAM
- **存储**: 20GB SSD
- **网络**: 100Mbps

### 推荐配置（生产环境）

- **CPU**: 4核+
- **内存**: 8GB+ RAM
- **存储**: 100GB+ SSD
- **网络**: 1Gbps

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.12+
- PostgreSQL 15+
- Redis 7+

---

## Docker Compose部署

### 1. 克隆仓库

```bash
git clone https://github.com/AyaseAlterego/ResonanceBeacon.git
cd ResonanceBeacon
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
cat > .env << EOF
# 数据库配置
DATABASE_URL=postgresql://postgres:your-strong-password@postgres:5432/hermes
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-strong-password
POSTGRES_DB=hermes

# Redis配置
REDIS_URL=redis://redis:6379/0

# 应用配置
ENVIRONMENT=production
SECRET_KEY=your-very-long-secret-key
API_KEY=your-api-key

# 日志级别
LOG_LEVEL=INFO

# 任务配置
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=600

# AI模型配置
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
EOF
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
docker-compose exec app alembic upgrade head

# 创建初始管理员用户
docker-compose exec app python -m hermes.认证 初始化管理员 --用户名 admin --密码 your-admin-password
```

### 5. 验证部署

```bash
# 检查健康状态
curl http://localhost:8000/api/v1/health

# 查看版本信息
curl http://localhost:8000/api/v1/version
```

---

## Kubernetes部署

### 1. 创建命名空间

```bash
kubectl create namespace hermes
```

### 2. 配置Secrets

```bash
# 创建数据库密码secret
kubectl create secret generic hermes-secrets \
  --namespace hermes \
  --from-literal=DATABASE_URL='postgresql://postgres:your-password@postgres:5432/hermes' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=SECRET_KEY='your-very-long-secret-key' \
  --from-literal=API_KEY='your-api-key' \
  --from-literal=ANTHROPIC_API_KEY='your-anthropic-api-key'
```

### 3. 部署PostgreSQL

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: hermes
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          value: hermes
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### 4. 部署Redis

```yaml
# redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: hermes
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
```

### 5. 部署应用

```yaml
# app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hermes-app
  namespace: hermes
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hermes
  template:
    metadata:
      labels:
        app: hermes
    spec:
      containers:
      - name: hermes
        image: your-registry/hermes:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: REDIS_URL
        - name: ENVIRONMENT
          value: production
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 6. 创建Service和Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: hermes-service
  namespace: hermes
spec:
  selector:
    app: hermes
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hermes-ingress
  namespace: hermes
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - hermes.your-domain.com
    secretName: hermes-tls
  rules:
  - host: hermes.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hermes-service
            port:
              number: 80
```

---

## 环境变量配置

### 必需变量

```bash
# 数据库连接URL
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis连接URL
REDIS_URL=redis://host:6379/0

# 应用密钥
SECRET_KEY=your-very-long-random-secret-key

# API密钥
API_KEY=your-api-key
```

### 可选变量

```bash
# 环境（development、staging、production）
ENVIRONMENT=production

# 日志级别（DEBUG、INFO、WARNING、ERROR）
LOG_LEVEL=INFO

# 最大并发任务数
MAX_CONCURRENT_TASKS=10

# 任务超时时间（秒）
TASK_TIMEOUT=600

# AI模型API密钥
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=9090

# CORS配置
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 数据库设置

### PostgreSQL配置

#### 生产环境推荐配置

```ini
# postgresql.conf
max_connections = 100
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB
random_page_cost = 1.1
effective_io_concurrency = 200
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
```

#### 创建数据库

```sql
-- 连接到PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE hermes;

-- 创建用户
CREATE USER hermes WITH PASSWORD 'your-password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE hermes TO hermes;

-- 连接到hermes数据库
\c hermes

-- 授予schema权限
GRANT ALL ON SCHEMA public TO hermes;
```

### 运行迁移

```bash
# 使用Alembic运行迁移
alembic upgrade head

# 或通过Docker
docker-compose exec app alembic upgrade head
```

---

## Redis设置

### Redis配置

```ini
# redis.conf
bind 0.0.0.0
port 6379
requirepass your-redis-password
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

### 验证Redis连接

```bash
# 测试连接
redis-cli -h localhost -p 6379 -a your-password ping

# 应该返回 PONG
```

---

## 反向代理配置

### Nginx配置

```nginx
# /etc/nginx/conf.d/hermes.conf
upstream hermes {
    server app:8000;
}

server {
    listen 80;
    server_name hermes.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hermes.your-domain.com;

    ssl_certificate /etc/nginx/ssl/hermes.crt;
    ssl_certificate_key /etc/nginx/ssl/hermes.key;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 代理配置
    location / {
        proxy_pass http://hermes;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90s;
        proxy_send_timeout 90s;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://hermes;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
    }

    # 静态文件
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查端点（不记录日志）
    location /api/v1/health {
        proxy_pass http://hermes;
        access_log off;
    }
}
```

### Traefik配置（Docker环境）

```yaml
# docker-compose.yml中添加标签
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.herpes.rule=Host(`hermes.your-domain.com`)"
      - "traefik.http.routers.herpes.entrypoints=websecure"
      - "traefik.http.routers.herpes.tls.certresolver=letsencrypt"
      - "traefik.http.services.herpes.loadbalancer.server.port=8000"
```

---

## SSL/TLS证书

### 使用Let's Encrypt

#### 安装Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

#### 获取证书

```bash
# 停止nginx
sudo systemctl stop nginx

# 获取证书
sudo certbot certonly --standalone -d hermes.your-domain.com

# 重启nginx
sudo systemctl start nginx
```

#### 自动续期

```bash
# 测试自动续期
sudo certbot renew --dry-run

# 添加crontab
sudo crontab -e
# 添加以下行（每天凌晨2点检查续期）
0 2 * * * certbot renew --post-hook "systemctl reload nginx"
```

---

## 监控和日志

### Prometheus监控

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hermes'
    static_configs:
      - targets: ['app:9090']
    metrics_path: '/metrics'
```

### Grafana仪表板

```bash
# 导入Hermes监控仪表板
# 访问 Grafana UI → Import → 输入仪表板ID
```

### 日志配置

```python
# logging.conf
[loggers]
keys=root,hermes

[handlers]
keys=console,file

[formatters]
keys=verbose

[logger_root]
level=INFO
handlers=console,file

[logger_hermes]
level=DEBUG
handlers=console,file
qualname=hermes
propagate=0

[handler_console]
class=StreamHandler
level=DEBUG
formatter=verbose
args=(sys.stdout,)

[handler_file]
class=RotatingFileHandler
level=INFO
formatter=verbose
args=('logs/hermes.log', 'a', 10485760, 5)

[formatter_verbose]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
```

### 日志轮转

```bash
# /etc/logrotate.d/hermes
/var/log/hermes/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 hermes hermes
    sharedscripts
    postrotate
        /usr/bin/systemctl reload hermes > /dev/null 2>&1 || true
    endscript
}
```

---

## 备份和恢复

### 数据库备份

#### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/hermes"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hermes_$DATE.sql.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -U postgres hermes | gzip > $BACKUP_FILE

# 保留最近7天的备份
find $BACKUP_DIR -name "hermes_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

#### 设置Crontab

```bash
# 每天凌晨3点执行备份
0 3 * * * /path/to/backup.sh >> /var/log/hermes-backup.log 2>&1
```

### 数据库恢复

```bash
# 恢复数据库
gunzip -c /backup/hermes/hermes_20240115_030000.sql.gz | psql -U postgres hermes
```

### Redis备份

```bash
# 触发Redis备份
redis-cli -a your-password BGSAVE

# 备份文件位置
/var/lib/redis/dump.rdb
```

---

## 性能调优

### 应用层调优

```bash
# 使用Gunicorn运行（推荐）
gunicorn hermes.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 600 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

### 数据库调优

```sql
-- 创建索引（如果不存在）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_流水线_状态 ON 流水线(状态);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_任务_阶段ID ON 任务(阶段ID);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_制品_流水线ID ON 制品(流水线ID);

-- 分析表以更新统计信息
ANALYZE 流水线;
ANALYZE 任务;
ANALYZE 制品;
```

### Redis调优

```bash
# 监控Redis性能
redis-cli info stats

# 清理过期键
redis-cli --scan --pattern "hermes:*" | head -20
```

---

## 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库服务
docker-compose ps postgres

# 检查数据库日志
docker-compose logs postgres

# 测试连接
psql -U postgres -h localhost -d hermes
```

#### 2. Redis连接失败

```bash
# 检查Redis服务
docker-compose ps redis

# 测试连接
redis-cli -h localhost -p 6379 ping
```

#### 3. 应用启动失败

```bash
# 检查应用日志
docker-compose logs app

# 检查环境变量
docker-compose exec app env | grep DATABASE_URL

# 检查数据库迁移
docker-compose exec app alembic current
```

#### 4. 内存不足

```bash
# 检查内存使用
docker stats

# 增加内存限制
# 修改docker-compose.yml中的deploy.resources.limits.memory
```

#### 5. 任务超时

```bash
# 增加超时时间
export TASK_TIMEOUT=1200

# 检查任务日志
docker-compose logs -f app | grep "timeout"
```

### 健康检查

```bash
# 系统健康检查
curl http://localhost:8000/api/v1/health

# 查看详细状态
curl http://localhost:8000/api/v1/version

# 检查智能体状态
curl http://localhost:8000/api/v1/agents
```

### 日志分析

```bash
# 查看错误日志
docker-compose logs app | grep ERROR

# 查看特定时间段的日志
docker-compose logs --since 2024-01-15T10:00:00 app

# 实时查看日志
docker-compose logs -f app
```

---

## 生产环境检查清单

### 部署前检查

- [ ] 环境变量已配置
- [ ] 数据库已创建并迁移
- [ ] Redis已启动并配置密码
- [ ] SSL/TLS证书已配置
- [ ] 反向代理已配置
- [ ] 防火墙已配置
- [ ] 备份已设置
- [ ] 监控已配置

### 安全检查

- [ ] 所有密码已更换为强密码
- [ ] API密钥已生成
- [ ] CORS已配置
- [ ] 速率限制已启用
- [ ] 日志已启用
- [ ] 审计日志已启用

### 性能检查

- [ ] 数据库连接池已配置
- [ ] Redis缓存已启用
- [ ] 静态文件已缓存
- [ ] Gunicorn worker数已调整
- [ ] 数据库索引已创建

### 监控检查

- [ ] 健康检查端点可访问
- [ ] Prometheus指标已导出
- [ ] Grafana仪表板已配置
- [ ] 告警规则已设置
- [ ] 日志收集已配置

---

## 更多资源

- [README.md](../README.md) - 项目概述
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南
- [API文档](./api.md) - API接口文档
- [examples/](../examples/) - 示例代码

---

## 支持

遇到问题？

- 查看 [GitHub Issues](https://github.com/AyaseAlterego/ResonanceBeacon/issues)
- 查看 [文档](https://github.com/AyaseAlterego/ResonanceBeacon/tree/main/docs)
- 提交新的Issue报告问题
