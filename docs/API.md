# VoicePut API 接口文档

## 基础信息

- **基础URL**: `http://localhost:51001`
- **API版本**: v1.1.0
- **内容类型**: `application/json`
- **认证方式**: 暂无（开发阶段）

## 通用响应格式

### 成功响应
```json
{
    "status": "success",
    "data": {},
    "message": "操作成功"
}
```

### 错误响应
```json
{
    "status": "error",
    "message": "错误描述",
    "code": "ERROR_CODE"
}
```

## API 接口列表

### 1. 系统状态接口

#### 1.1 健康检查
- **URL**: `/health`
- **方法**: `GET`
- **描述**: 检查系统健康状态

**响应示例**:
```json
{
    "status": "healthy"
}
```

#### 1.2 系统状态
- **URL**: `/api/status`
- **方法**: `GET`
- **描述**: 获取详细系统状态

**响应示例**:
```json
{
    "status": "running",
    "time": "2025-07-01 15:30:00",
    "version": "1.1.0"
}
```

### 2. 对话接口

#### 2.1 文本对话
- **URL**: `/api/chat`
- **方法**: `POST`
- **描述**: 发送文本消息与AI对话

**请求参数**:
```json
{
    "text": "你好，今天天气怎么样？",
    "role_id": "nekogirl",
    "stream": true
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| text | string | 是 | 用户输入的文本 |
| role_id | string | 否 | 角色ID，不填使用当前角色 |
| stream | boolean | 否 | 是否使用流式输出，默认true |

**响应示例**:
```json
{
    "response": "你好！今天天气很不错呢，阳光明媚，适合出去走走哦~"
}
```

#### 2.2 直接模型对话
- **URL**: `/api/direct-chat`
- **方法**: `POST`
- **描述**: 直接与模型对话，不触发语音合成

**请求参数**: 同 `/api/chat`

**响应示例**: 同 `/api/chat`

### 3. 语音识别接口

#### 3.1 语音识别
- **URL**: `/api/voice/recognize`
- **方法**: `POST`
- **描述**: 将音频数据转换为文本

**请求参数**:
```json
{
    "audio_data": "base64_encoded_audio_data"
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| audio_data | string | 是 | Base64编码的音频数据 |

**响应示例**:
```json
{
    "recognized_text": "你好，今天天气怎么样",
    "status": "success"
}
```

#### 3.2 直接语音识别
- **URL**: `/api/direct-recognize`
- **方法**: `POST`
- **描述**: 直接语音识别，不触发自动回复

**请求参数**: 同 `/api/voice/recognize`

**响应示例**: 同 `/api/voice/recognize`

### 4. 语音合成接口

#### 4.1 文本转语音
- **URL**: `/api/voice/speak`
- **方法**: `POST`
- **描述**: 将文本转换为语音

**请求参数**:
```json
{
    "text": "你好，很高兴见到你！",
    "role_id": "libai"
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| text | string | 是 | 要转换的文本 |
| role_id | string | 否 | 角色ID，不填使用当前角色 |

**响应示例**:
```json
{
    "audio_paths": [
        "/static/audio/temp_1625123456.mp3"
    ],
    "status": "success"
}
```

### 5. 角色管理接口

#### 5.1 获取角色列表
- **URL**: `/api/roles`
- **方法**: `GET`
- **描述**: 获取所有可用的语音角色

**响应示例**:
```json
{
    "roles": [
        {
            "id": "libai",
            "name": "李白模拟",
            "voice": "longshu-v2",
            "character_id": "e2eed5eed7bb4fa8a75a7b4cfc8fb235"
        },
        {
            "id": "nekogirl",
            "name": "猫娘",
            "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6",
            "character_id": "5ffe587bb14941cda6012bffe3ac3f46"
        }
    ]
}
```

#### 5.2 设置当前角色
- **URL**: `/api/role/set`
- **方法**: `POST`
- **描述**: 设置当前使用的语音角色

**请求参数**:
```json
{
    "role_id": "dongxuelian"
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| role_id | string | 是 | 要设置的角色ID |

**响应示例**:
```json
{
    "status": "success",
    "message": "已设置角色为 dongxuelian"
}
```

### 6. 控制接口

#### 6.1 中断AI语音
- **URL**: `/api/interrupt`
- **方法**: `POST`
- **描述**: 中断当前正在播放的AI语音

**响应示例**:
```json
{
    "status": "success",
    "message": "AI响应已中断"
}
```

#### 6.2 强制关闭服务
- **URL**: `/shutdown`
- **方法**: `POST`
- **描述**: 强制关闭服务器（谨慎使用）

**响应示例**:
```json
{
    "status": "success",
    "message": "服务器正在关闭..."
}
```

## 支持的角色列表

| 角色ID | 角色名称 | 语音特色 | 适用场景 |
|--------|----------|----------|----------|
| libai | 李白模拟 | 古风男声，诗意浓厚 | 诗词创作、文学讨论 |
| nekogirl | 猫娘 | 可爱女声，萌系风格 | 轻松聊天、娱乐互动 |
| dongxuelian | 东雪莲 | 温柔女声，知性优雅 | 正式对话、学习辅导 |
| yunli | 云璃 | 清澈女声，清新自然 | 日常交流、情感支持 |
| storyteller | 讲故事的人 | 磁性中性，富有感染力 | 故事叙述、内容播报 |
| direct_model | 直接模型 | 标准男声，专业严谨 | 技术咨询、信息查询 |

## 错误代码说明

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| INVALID_PARAMETER | 400 | 请求参数无效 |
| ROLE_NOT_FOUND | 404 | 指定的角色不存在 |
| AUDIO_PROCESS_ERROR | 500 | 音频处理失败 |
| ASR_SERVICE_ERROR | 500 | 语音识别服务错误 |
| TTS_SERVICE_ERROR | 500 | 语音合成服务错误 |
| MODEL_SERVICE_ERROR | 500 | AI模型服务错误 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |

## 音频格式要求

### 输入音频（语音识别）
- **格式**: WAV, MP3
- **采样率**: 16kHz（推荐）
- **声道**: 单声道
- **编码**: Base64
- **最大大小**: 10MB

### 输出音频（语音合成）
- **格式**: MP3
- **采样率**: 22.05kHz
- **比特率**: 128kbps
- **声道**: 单声道

## 使用示例

### JavaScript 示例

```javascript
// 文本对话
async function chatWithAI(text, roleId = null) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            role_id: roleId,
            stream: true
        })
    });
    
    const result = await response.json();
    return result.response;
}

// 语音识别
async function recognizeAudio(audioBlob) {
    const base64Audio = await blobToBase64(audioBlob);
    
    const response = await fetch('/api/voice/recognize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            audio_data: base64Audio
        })
    });
    
    const result = await response.json();
    return result.recognized_text;
}

// 语音合成
async function synthesizeVoice(text, roleId = null) {
    const response = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            role_id: roleId
        })
    });
    
    const result = await response.json();
    return result.audio_paths;
}

// 工具函数：Blob转Base64
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}
```

### Python 示例

```python
import requests
import base64

class VoicePutClient:
    def __init__(self, base_url="http://localhost:51001"):
        self.base_url = base_url
    
    def chat(self, text, role_id=None, stream=True):
        """文本对话"""
        url = f"{self.base_url}/api/chat"
        data = {
            "text": text,
            "stream": stream
        }
        if role_id:
            data["role_id"] = role_id
            
        response = requests.post(url, json=data)
        return response.json()
    
    def recognize_audio(self, audio_file_path):
        """语音识别"""
        with open(audio_file_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()
        
        url = f"{self.base_url}/api/voice/recognize"
        data = {"audio_data": audio_data}
        
        response = requests.post(url, json=data)
        return response.json()
    
    def synthesize_voice(self, text, role_id=None):
        """语音合成"""
        url = f"{self.base_url}/api/voice/speak"
        data = {"text": text}
        if role_id:
            data["role_id"] = role_id
            
        response = requests.post(url, json=data)
        return response.json()
    
    def get_roles(self):
        """获取角色列表"""
        url = f"{self.base_url}/api/roles"
        response = requests.get(url)
        return response.json()
    
    def set_role(self, role_id):
        """设置角色"""
        url = f"{self.base_url}/api/role/set"
        data = {"role_id": role_id}
        response = requests.post(url, json=data)
        return response.json()

# 使用示例
client = VoicePutClient()

# 对话
result = client.chat("你好，今天天气怎么样？", role_id="nekogirl")
print(result["response"])

# 获取角色列表
roles = client.get_roles()
print(roles["roles"])
```

## 注意事项

1. **API速率限制**: 目前暂无限制，生产环境建议添加
2. **音频文件管理**: 系统会自动清理临时音频文件
3. **会话管理**: 系统支持多会话，会话ID自动生成
4. **错误处理**: 建议在客户端实现重试机制
5. **CORS**: 开发环境已配置允许所有来源，生产环境需要限制

## 更新日志

### v1.1.0 (2025-07-01)
- 添加数据库支持
- 优化音频处理性能
- 增加新的角色支持
- 完善错误处理机制

### v1.0.0 (2025-06-01)
- 初始版本发布
- 基础的语音识别和合成功能
- 多角色支持
- Web API接口
