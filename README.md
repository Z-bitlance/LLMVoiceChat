# VoicePut - 智能语音对话系统

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 项目简介

VoicePut 是一个基于 Python 开发的智能语音对话系统，集成了实时语音识别（ASR）、文本转语音（TTS）和大语言模型对话功能。系统支持多角色语音合成，具备完整的 Web API 接口，可实现自然流畅的人机语音交互。

### ✨ 核心特性

- 🎤 **实时语音识别**：基于阿里云 DashScope ASR 引擎，支持实时语音转文字
- 🔊 **多角色语音合成**：基于cosyvoice-v2,支持多种声音角色，包括李白、~~猫娘~~、~~东雪莲~~等个性化角色，可在voicecopy自行添加，详情参考https://help.aliyun.com/zh/model-studio/cosyvoice-clone-api
- 🤖 **智能对话**：集成大语言模型，支持上下文记忆的自然对话 //(上下文待添加)
- 🌐 **Web API 接口**：完整的 RESTful API，支持前后端分离
- 💾 **数据持久化**：SQLite 数据库存储对话历史和用户偏好 //(未上线)
- 🎛️ **并发处理**：多线程音频处理，支持实时语音流
- 🔄 **流式处理**：支持音频分段处理和播放
- 📱 **跨平台兼容**：支持 Web 端和移动端访问

## 🏗️ 系统架构

```
VoicePut/
├── voice-web-backend/          # 后端服务
│   └── backend/
│       ├── api/                # API 路由
│       │   └── routes_new.py   # 主要API接口
│       ├── core/               # 核心模块
│       │   ├── dialogue_manager_new.py  # 对话管理器
│       │   ├── agentChat.py    # AI对话代理
│       │   ├── asr.py          # 语音识别
│       │   ├── voiceSpeak.py   # 语音合成
│       │   ├── db_manager.py   # 数据库管理
│       │   └── playMp3.py      # 音频播放
│       ├── static/             # 静态文件
│       │   ├── audio/          # 音频文件存储
│       │   ├── logs/           # 日志文件
│       │   └── data/           # 数据库文件
│       └── main_new.py         # 应用入口
├── voice-web-frontend/         # 前端界面
├── VoiceData/                  # 音频数据存储
└── docs/                       # 文档目录
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- pip 或 uv 包管理器
- 阿里云 DashScope API Key

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd VoicePut
```

2. **安装依赖**
```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv
uv sync
```

3. **配置环境变量**
```bash
# 设置阿里云 API Key
export DASHSCOPE_API_KEY="your-api-key-here"
```

4. **启动后端服务**
```bash
cd voice-web-backend/backend
python main_new.py
```

5. **启动前端服务**
```bash
cd voice-web-frontend
npm i
npm run dev
```

6. **访问服务**
- API 文档: http://localhost:{port}/docs
- 健康检查: http://localhost:{port}/health

### Docker 部署（可选）

```bash
# 构建镜像
docker build -t voiceput .

# 运行容器
docker run -p 51001:51001 -e DASHSCOPE_API_KEY="your-key" voiceput
```

## 📚 API 接口文档

### 基础接口

#### 1. 文本对话
```http
POST /api/chat
Content-Type: application/json

{
    "text": "你好，今天天气怎么样？",
    "role_id": "nekogirl",
    "stream": true
}
```

#### 2. 语音识别
```http
POST /api/voice/recognize
Content-Type: application/json

{
    "audio_data": "base64_encoded_audio_data"
}
```

#### 3. 语音合成
```http
POST /api/voice/speak
Content-Type: application/json

{
    "text": "你好，很高兴见到你！",
    "role_id": "libai"
}
```

#### 4. 获取角色列表
```http
GET /api/roles
```

#### 5. 设置当前角色
```http
POST /api/role/set
Content-Type: application/json

{
    "role_id": "dongxuelian"
}
```

#### 6. 中断AI语音
```http
POST /api/interrupt
```

#### 7. 系统状态
```http
GET /api/status
```

#### 8. 强制关闭服务
```http
POST /shutdown
```

### 响应格式

成功响应:
```json
{
    "response": "AI的回复内容",
    "status": "success"
}
```

错误响应:
```json
{
    "status": "error",
    "message": "错误描述"
}
```

## 🎭 支持的角色

| 角色ID | 角色名称 | 语音特色 | 角色描述 |
|--------|----------|----------|----------|
| libai | 李白模拟 | 古风男声 | 模拟唐代诗人李白的说话风格 |
| nekogirl | 猫娘 | 可爱女声 | ~~二次元猫娘角色，语气可爱~~ |
| dongxuelian | ~~东雪莲~~ | 温柔女声 | ~~温柔知性的~~女性角色 |
| ~~yunli~~| ~~云璃~~ | 清澈女声 | 清新自然的女性角色 | （未添加）
| storyteller | 讲故事的人 | 磁性中性 | 适合讲故事的声音 | （未添加）
| direct_model | 直接模型 | 标准男声 | 标准的AI助手声音 | （未添加）

## 💾 数据库设计

系统使用 SQLite 数据库存储以下信息：

### 对话历史表 (conversations)
- id: 主键
- session_id: 会话ID
- user_input: 用户输入
- ai_response: AI回复
- role_id: 使用的角色
- timestamp: 时间戳
- additional_data: 额外数据

### 用户偏好表 (user_preferences)
- id: 主键
- user_id: 用户ID
- preferred_role: 偏好角色
- voice_settings: 语音设置
- last_login: 最后登录时间
- settings_json: 其他设置

### 角色配置表 (role_configs)
- id: 主键
- role_id: 角色ID
- role_name: 角色名称
- voice_id: 语音ID
- character_id: 性格ID
- config_json: 配置信息

## 🔧 配置说明

### 主要配置文件

1. **main_new.py** - 应用主配置
   - 端口设置: `PORT=51001`
   - CORS 配置
   - 静态文件路径

2. **dialogue_manager_new.py** - 对话管理器配置
   - API Key 配置
   - 音频参数设置
   - 线程管理配置

3. **voiceSpeak.py** - 语音合成配置
   - TTS API 地址
   - 音频文件存储路径
   - 角色语音配置

### 环境变量

```bash
# 必需配置
DASHSCOPE_API_KEY=your_api_key_here

# 可选配置
PORT=51001
HOST=0.0.0.0
DEBUG=false
## 🧪 测试说明

### 单元测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_dialogue_manager.py
```

### API 测试
使用提供的 Postman Collection 或直接访问 `/docs` 页面进行接口测试。

### 功能测试
1. 语音识别测试：录制音频文件，通过API上传测试
2. 语音合成测试：发送文本，检查生成的音频文件
3. 对话测试：测试多轮对话的上下文记忆
4. 角色切换测试：测试不同角色的语音效果

## 🛠️ 开发指南

### 添加新角色

1. 在 `dialogue_manager_new.py` 的 `get_supported_roles()` 方法中添加角色信息
2. 配置对应的语音ID和性格ID
3. 更新数据库角色配置表

### 扩展API接口

1. 在 `routes_new.py` 中添加新的路由
2. 实现对应的业务逻辑
3. 更新API文档

### 性能优化

1. **音频处理优化**：使用音频流式处理减少延迟
2. **并发优化**：合理使用线程池处理并发请求
3. **缓存策略**：缓存常用的音频文件和对话结果
4. **数据库优化**：添加适当的索引，优化查询语句

## 📱 移动端部署

### Web App 方式
1. 确保后端服务可外网访问
2. 配置 HTTPS 证书
3. 开发响应式前端界面
4. 添加 PWA 配置

### 原生应用
1. 开发 Android/iOS 客户端
2. 集成录音和播放功能
3. 调用后端 API 接口
4. 处理网络和权限问题

## 🔍 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 确认Python版本和依赖包
   - 查看错误日志

2. **语音识别失败**
   - 检查API Key是否正确
   - 确认网络连接
   - 验证音频格式和大小

3. **语音合成无声音**
   - 检查TTS服务是否运行
   - 确认音频文件路径
   - 验证播放器配置

4. **数据库错误**
   - 检查数据库文件权限
   - 确认表结构是否正确
   - 查看数据库日志

### 日志查看

```bash
# 查看应用日志
tail -f backend/static/logs/app.log

# 查看对话历史
ls backend/static/logs/conversation_*.json

# 查看会话记录
ls backend/static/logs/sessionID_*.json
```

## 📈 性能监控

### 关键指标
- API 响应时间
- 语音识别准确率
- 音频处理延迟
- 并发用户数
- 错误率统计

### 监控工具
- 使用 Prometheus + Grafana 进行指标监控
- 使用 ELK 栈进行日志分析
- 使用 APM 工具进行性能跟踪

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交 Pull Request

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档
- 编写单元测试
- 使用类型提示

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- **主要开发者** - [Z-bitlance]

## 🙏 致谢

- 阿里云 DashScope 提供的AI服务
- FastAPI 框架
- 所有贡献者和测试用户

## 📞 支持

如有问题或建议，请通过以下方式联系：

~~- 提交 Issue: [GitHub Issues](link-to-issues)~~
~~- 邮箱: your-email@example.com~~
~~- 文档: [在线文档](link-to-docs)~~

---

**注意**: 本项目仅供学习和研究使用，请确保遵守相关的服务条款和隐私政策。
