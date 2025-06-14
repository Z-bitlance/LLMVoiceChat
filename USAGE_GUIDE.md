# AI语音对话系统使用指南

## 系统概述

AI语音对话系统是一个集成了语音识别、语音合成和AI大语言模型的交互系统，支持多种角色和实时语音交互。

## 系统架构

系统分为三个主要部分：

1. **语音合成服务** (`voiceOut.py`)：提供文本到语音的转换
2. **后端API服务** (`voice-chat-web/backend`)：处理对话逻辑、角色管理等
3. **前端界面** (`voice-web-frontend`)：用户交互界面

## 快速启动

### 1. 启动语音合成服务

```powershell
cd d:\pythonprojects\pythonProject\model\VoicePut
python voiceOut.py
```

这将启动一个运行在51000端口的TTS服务。

### 2. 启动后端API服务

```powershell
cd d:\pythonprojects\pythonProject\model\VoicePut
.\start_voice_chat_web.bat
```

这将启动一个运行在8000端口的后端API服务。

### 3. 启动前端服务

```powershell
cd d:\pythonprojects\pythonProject\model\VoicePut
.\start_voice_frontend.bat
```

或者手动启动：

```powershell
cd d:\pythonprojects\pythonProject\model\VoicePut\voice-web-frontend
npm run dev
```

这将启动前端开发服务器，通常运行在3000端口。

## 使用方法

### 角色选择

系统支持多种预定义角色，每个角色有不同的语音风格：

- **AI助手**（默认）：使用"龙翔"声音
- **教师**：使用"小云"声音
- **医生**：使用"艾夏"声音
- **客服**：使用"若溪"声音
- **讲故事的人**：使用"思佳"声音
- **直接模型**：直接连接到后端配置的AI模型

### 文本对话

1. 在输入框中输入文本
2. 点击"发送"按钮
3. 系统将处理文本并播放AI回复的语音

### 语音对话

1. 点击麦克风按钮开始录音
2. 说话后点击停止录音
3. 系统将识别语音并播放AI回复

### 中断AI语音

在AI回答过程中，您可以：

1. 点击红色停止按钮中断当前语音
2. 开始新的录音自动中断之前的语音

## 音频播放机制

系统使用以下机制处理和播放音频：

1. **后端处理**：
   - AI回答被分割成多个短句
   - 每个短句被转换为MP3音频文件
   - 文件保存在`backend/static/audio/`目录

2. **前端播放**：
   - 前端接收音频文件的URL列表
   - 按顺序播放每个音频文件
   - 支持中断当前正在播放的音频

## 故障排除

### 音频无法播放

- 确认语音合成服务(voiceOut.py)正在运行
- 检查浏览器控制台是否有错误信息
- 确认音频文件路径正确且可访问

### 语音识别不工作

- 确保浏览器允许麦克风访问权限
- 检查语音识别服务是否正常运行

### 系统响应缓慢

- 可能是大模型处理时间较长
- 检查网络连接是否正常
- 确认后端服务器负载是否过高

## 高级配置

可以通过修改以下文件进行系统配置：

- `backend/.env`：后端环境配置
- `voice-web-frontend/.env`：前端环境配置

## 数据存储

对话内容会保存在以下位置：

- 短期存储：浏览器本地存储
- 长期存储：`backend/static/logs/`目录中的JSON文件

## 注意事项

- 系统需要网络连接才能使用AI大模型
- 音频文件会临时占用磁盘空间，可定期清理`static/audio`目录
