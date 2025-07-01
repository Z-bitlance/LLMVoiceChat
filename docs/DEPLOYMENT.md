# VoicePut 部署指南

## 📋 部署前准备

### 系统要求
- **操作系统**: Windows 10+, Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.11 或更高版本
- **内存**: 最低 4GB，推荐 8GB+
- **存储**: 最低 2GB 可用空间
- **网络**: 稳定的互联网连接（用于调用AI服务）

### 必需的外部服务
- **阿里云 DashScope API**: 用于语音识别和AI对话
- **TTS 服务**: 语音合成服务（端口 51000）

## 🚀 本地开发部署

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd VoicePut

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 2. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 或使用 uv（推荐）
pip install uv
uv sync
```

### 3. 环境配置

创建 `.env` 文件：
```bash
# .env
DASHSCOPE_API_KEY=your_api_key_here
PORT=51001
HOST=0.0.0.0
DEBUG=true
```

### 4. 启动服务

```bash
# 启动后端服务
cd voice-web-backend/backend
python main_new.py

# 服务将在 http://localhost:51001 启动
```

### 5. 验证部署

```bash
# 检查健康状态
curl http://localhost:51001/health

# 查看API文档
# 访问 http://localhost:51001/docs
```

## 🐳 Docker 部署

### 1. 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p backend/static/audio backend/static/logs backend/static/data

# 暴露端口
EXPOSE 51001

# 设置环境变量
ENV PYTHONPATH=/app/voice-web-backend/backend

# 启动命令
CMD ["python", "voice-web-backend/backend/main_new.py"]
```

### 2. 构建和运行

```bash
# 构建镜像
docker build -t voiceput:latest .

# 运行容器
docker run -d \
  --name voiceput \
  -p 51001:51001 \
  -e DASHSCOPE_API_KEY="your_api_key" \
  -v $(pwd)/data:/app/backend/static \
  voiceput:latest

# 查看日志
docker logs -f voiceput
```

### 3. Docker Compose 部署

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  voiceput:
    build: .
    ports:
      - "51001:51001"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - DEBUG=false
    volumes:
      - ./data:/app/backend/static
      - ./logs:/app/backend/static/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:51001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - voiceput
    restart: unless-stopped

volumes:
  data:
  logs:
```

启动服务：
```bash
# 创建环境变量文件
echo "DASHSCOPE_API_KEY=your_api_key" > .env

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

## ☁️ 云服务器部署

### 1. 服务器选择

推荐配置：
- **CPU**: 2核心以上
- **内存**: 4GB 以上
- **存储**: 20GB SSD
- **带宽**: 5Mbps 以上

### 2. 服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget vim htop

# 安装 Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装音频依赖
sudo apt install -y portaudio19-dev python3-dev gcc g++
```

### 3. 应用部署

```bash
# 创建应用用户
sudo useradd -m -s /bin/bash voiceput
sudo su - voiceput

# 克隆项目
git clone <repository-url> ~/voiceput
cd ~/voiceput

# 设置虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置正确的 API Key
```

### 4. 系统服务配置

创建 systemd 服务文件：

```bash
# /etc/systemd/system/voiceput.service
[Unit]
Description=VoicePut Voice Chat System
After=network.target

[Service]
Type=simple
User=voiceput
Group=voiceput
WorkingDirectory=/home/voiceput/voiceput
Environment=PATH=/home/voiceput/voiceput/venv/bin
EnvironmentFile=/home/voiceput/voiceput/.env
ExecStart=/home/voiceput/voiceput/venv/bin/python voice-web-backend/backend/main_new.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启用自启动
sudo systemctl enable voiceput

# 启动服务
sudo systemctl start voiceput

# 查看状态
sudo systemctl status voiceput
```

### 5. Nginx 反向代理

安装 Nginx：
```bash
sudo apt install -y nginx
```

配置反向代理（`/etc/nginx/sites-available/voiceput`）：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:51001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件
    location /static/ {
        alias /home/voiceput/voiceput/voice-web-backend/backend/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/voiceput /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL 证书配置

使用 Let's Encrypt：
```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔒 安全配置

### 1. 防火墙设置

```bash
# UFW 防火墙
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. 应用安全

在 `main_new.py` 中添加安全配置：
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# 添加安全中间件
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
app.add_middleware(HTTPSRedirectMiddleware)  # 生产环境启用

# 限制 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. API 限流

安装并配置 slowapi：
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 在路由中使用
@router.post("/chat")
@limiter.limit("10/minute")  # 每分钟最多10次请求
async def chat_with_ai(request: Request, input_data: UserInput):
    # ...
```

## 📊 监控和日志

### 1. 日志配置

创建日志配置文件 `logging.conf`：
```ini
[loggers]
keys=root,voiceput

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_voiceput]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=voiceput
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=simpleFormatter
args=('logs/voiceput.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 2. 健康检查

创建健康检查脚本 `health_check.sh`：
```bash
#!/bin/bash

URL="http://localhost:51001/health"
TIMEOUT=10

response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT $URL)

if [ "$response" = "200" ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    exit 1
fi
```

### 3. 系统监控

使用 Prometheus + Grafana：
```python
# 安装依赖
pip install prometheus-client

# 在应用中添加指标
from prometheus_client import Counter, Histogram, generate_latest

# 定义指标
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

# 添加监控端点
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔄 持续部署

### 1. GitHub Actions

创建 `.github/workflows/deploy.yml`：
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: pytest
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /home/voiceput/voiceput
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart voiceput
```

### 2. 回滚策略

创建回滚脚本 `rollback.sh`：
```bash
#!/bin/bash

BACKUP_DIR="/home/voiceput/backups"
CURRENT_DIR="/home/voiceput/voiceput"

# 获取最新备份
LATEST_BACKUP=$(ls -t $BACKUP_DIR | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "No backup found"
    exit 1
fi

# 停止服务
sudo systemctl stop voiceput

# 备份当前版本
cp -r $CURRENT_DIR $BACKUP_DIR/current_$(date +%Y%m%d_%H%M%S)

# 恢复备份
rm -rf $CURRENT_DIR/*
cp -r $BACKUP_DIR/$LATEST_BACKUP/* $CURRENT_DIR/

# 重启服务
sudo systemctl start voiceput

echo "Rollback completed to $LATEST_BACKUP"
```

## 📱 移动端部署

### 1. PWA 配置

创建 `manifest.json`：
```json
{
  "name": "VoicePut",
  "short_name": "VoicePut",
  "description": "智能语音对话系统",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 2. Service Worker

创建 `sw.js`：
```javascript
const CACHE_NAME = 'voiceput-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});
```

## ⚠️ 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   sudo netstat -tlnp | grep 51001
   
   # 检查权限
   sudo chown -R voiceput:voiceput /home/voiceput/voiceput
   
   # 查看详细日志
   sudo journalctl -u voiceput -f
   ```

2. **API 调用失败**
   ```bash
   # 检查 API Key
   echo $DASHSCOPE_API_KEY
   
   # 测试网络连接
   curl -I https://dashscope.aliyuncs.com
   
   # 检查防火墙
   sudo ufw status
   ```

3. **音频处理问题**
   ```bash
   # 安装音频依赖
   sudo apt install -y portaudio19-dev
   
   # 检查音频设备
   aplay -l
   
   # 测试音频播放
   python -c "import pyaudio; print('PyAudio OK')"
   ```

### 性能优化

1. **数据库优化**
   ```sql
   -- 添加索引
   CREATE INDEX idx_conversations_session_id ON conversations(session_id);
   CREATE INDEX idx_conversations_timestamp ON conversations(timestamp);
   ```

2. **缓存配置**
   ```python
   # 添加 Redis 缓存
   pip install redis
   
   # 缓存配置
   import redis
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   ```

3. **负载均衡**
   ```nginx
   upstream voiceput_backend {
       server 127.0.0.1:51001;
       server 127.0.0.1:51002;
       server 127.0.0.1:51003;
   }
   
   server {
       location / {
           proxy_pass http://voiceput_backend;
       }
   }
   ```

## 📞 支持

如果在部署过程中遇到问题，请：

1. 查看 [故障排除文档](troubleshooting.md)
2. 提交 [GitHub Issue](https://github.com/yourusername/voiceput/issues)
3. 联系技术支持: support@example.com

---

**注意**: 本指南适用于 VoicePut v1.1.0，不同版本可能有所差异。
