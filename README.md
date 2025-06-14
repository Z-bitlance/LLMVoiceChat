# 语音对话系统

这是一个结合了语音识别、语音合成和AI大模型的语音对话系统。

## 系统构成

系统由以下几个主要组件构成：

1. **后端API服务**：基于FastAPI的Web服务，提供聊天、语音合成等功能
2. **语音合成服务**：提供文本到语音的转换能力
3. **前端界面**：Vue.js编写的用户界面，包含多种角色和语音交互功能

## 系统目录结构

```
model/VoicePut/
├── agentChat.py              // 大模型聊天代理
├── playMp3.py               // 音频播放器
├── voiceOut.py              // 语音合成服务
├── voiceChatManage.py       // 语音对话管理
├── direct_model_api.py      // 直接模型API服务
├── voice-chat-web/          // Web后端服务
│   └── backend/
│       ├── main.py          // 主入口
│       ├── api/             // API路由
│       └── core/            // 核心功能
├── voice-web-frontend/      // Web前端
```

## 启动步骤

### 1. 启动语音合成服务

打开终端，运行：

```bash
# Windows
python voiceOut.py

# Linux/Mac
python3 voiceOut.py
```

这将启动一个运行在51000端口的TTS服务。

### 2. 启动后端API服务

使用提供的启动脚本：

```bash
# Windows
start_voice_chat_web.bat

# Linux/Mac
chmod +x start_voice_chat_web.sh
./start_voice_chat_web.sh
```

这将启动一个运行在8000端口的后端API服务。

### 3. 启动前端服务

使用提供的启动脚本：

```bash
# Windows
start_voice_frontend.bat

# Linux/Mac
chmod +x start_voice_frontend.sh
./start_voice_frontend.sh
```

这将启动前端开发服务器，通常运行在3000端口。

## 使用方法

1. 打开浏览器，访问 `http://localhost:3000`
2. 选择一个角色（助手、教师、医生等）
3. 输入文本进行对话，或使用麦克风进行语音输入
4. 系统将处理输入，调用AI模型生成回复，并通过语音合成进行播放

## API接口

主要API接口包括：

- `/api/chat` - 文本聊天
- `/api/voice/speak` - 文本转语音
- `/api/voice/recognize` - 语音识别
- `/api/roles` - 获取角色列表
- `/api/status` - 获取系统状态

## 音频传输与播放机制

系统使用以下机制处理和播放音频：

1. **音频生成**：
   - 后端通过TTS API将文本转换为MP3文件
   - 文件保存在`backend/static/audio/`目录中

2. **音频传输**：
   - 后端返回相对URL路径（如`/static/audio/temp_123456789.mp3`）
   - 前端根据这些URL请求音频文件

3. **音频播放**：
   - 前端使用HTML5 Audio API顺序播放收到的音频
   - 前端API提供`playAudio`和`playAudioSequentially`辅助函数

## 直接模型通信

除了常规API外，系统还支持直接与模型通信：

- `/api/direct-chat` - 直接连接到模型的文本聊天
- `/api/direct-recognize` - 直接连接到模型的语音识别

## 常见问题

1. **音频无法播放**：
   - 检查TTS服务是否正常运行（端口51000）
   - 检查浏览器控制台是否有跨域错误

2. **语音识别不工作**：
   - 确保浏览器允许麦克风访问权限
   - 检查音频格式是否正确

3. **模型响应慢**：
   - 可能是大模型服务负载高
   - 尝试使用直接模型通信

## 依赖项

安装依赖：

```bash
# 后端依赖
cd voice-web-backend/backend
pip install -r requirements.txt

# 前端依赖
cd voice-web-frontend
npm install
```
