import axios from 'axios';

// 读取环境变量
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const apiTimeout = parseInt(import.meta.env.VITE_API_TIMEOUT || '20000');

// 直接模型API地址（简化版）
const directModelUrl = 'http://localhost:51001';

// 本地后端API地址
const localBackendUrl = 'http://localhost:51001/api';

// 创建axios实例
const apiClient = axios.create({
  baseURL: localBackendUrl,
  timeout: apiTimeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url);
    // 为每个请求添加时间戳，避免缓存
    const timestamp = new Date().getTime();
    config.url = config.url.includes('?') 
      ? `${config.url}&_t=${timestamp}` 
      : `${config.url}?_t=${timestamp}`;
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 重试配置
const MAX_RETRIES = 2;
const retryDelay = (retryCount) => {
  return retryCount * 1000; // 1秒, 2秒, ...
};

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response.data;
  },
  async error => {
    const config = error.config;
    
    // 如果没有重试次数字段，添加它
    if (!config || !config.retry) {
      config.retry = 0;
    }
    
    // 如果重试次数小于最大重试次数，并且错误是网络错误或5xx服务器错误
    if (
      config.retry < MAX_RETRIES && 
      (error.message.includes('Network Error') || 
       (error.response && error.response.status >= 500))
    ) {
      config.retry += 1;
      
      // 延迟重试
      const delay = retryDelay(config.retry);
      console.warn(`第${config.retry}次重试请求: ${config.url}, 延迟${delay}ms`);
      
      // 延迟后重试
      return new Promise(resolve => {
        setTimeout(() => {
          resolve(apiClient(config));
        }, delay);
      });
    }
    
    // 格式化错误消息
    let errorMessage = '请求失败';
    if (error.response) {
      // 服务端返回的错误
      switch (error.response.status) {
        case 400:
          errorMessage = '请求参数错误';
          break;
        case 401:
          errorMessage = '未授权，请重新登录';
          break;
        case 403:
          errorMessage = '拒绝访问';
          break;
        case 404:
          errorMessage = '请求的资源不存在';
          break;
        case 500:
          errorMessage = '服务器内部错误';
          break;
        default:
          errorMessage = `请求错误 (${error.response.status})`;
      }
      console.error('API错误:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求发出但没有收到响应
      errorMessage = '服务器无响应';
      console.error('无响应:', error.request);
    } else {
      // 请求配置错误
      errorMessage = error.message;
      console.error('请求配置错误:', error.message);
    }
    
    error.userMessage = errorMessage;
    return Promise.reject(error);
  }
);

// 音频处理辅助函数
const playAudio = (audioUrl) => {
  return new Promise((resolve, reject) => {
    try {
      // 创建音频元素
      const audio = new Audio(localBackendUrl.replace(/\/api$/, '') + audioUrl);
      
      // 监听事件
      audio.onended = () => {
        resolve();
      };
      
      audio.onerror = (error) => {
        console.error('音频播放错误:', error);
        reject(error);
      };
      
      // 开始播放
      audio.play();
    } catch (error) {
      console.error('创建音频播放器失败:', error);
      reject(error);
    }
  });
};

// 按顺序播放多个音频文件
const playAudioSequentially = async (audioUrls) => {
  for (const url of audioUrls) {
    try {
      await playAudio(url);
    } catch (error) {
      console.error(`播放音频 ${url} 失败:`, error);
    }
  }
};

// API函数

/**
 * 获取系统状态
 */
export const getSystemStatus = async () => {
  return apiClient.get('/status');
};

/**
 * 获取支持的角色列表
 */
export const getRoles = async () => {
  return apiClient.get('/roles');
};

/**
 * 设置当前角色
 * @param {string} roleId 角色ID
 */
export const setRole = async (roleId) => {
  return apiClient.post('/role/set', { role_id: roleId });
};

/**
 * 发送聊天消息
 * @param {string} text 文本内容
 * @param {string} roleId 角色ID
 * @param {boolean} autoPlay 是否自动播放音频
 */
export const sendChatMessage = async (text, roleId, autoPlay = true) => {
  const response = await apiClient.post('/chat', { 
    text, 
    role_id: roleId,
    stream: false
  });
  
  if (autoPlay && response.audio_urls && response.audio_urls.length > 0) {
    // 自动播放返回的音频
    playAudioSequentially(response.audio_urls);
  }
  
  return response;
};

/**
 * 语音识别
 * @param {string} audioData Base64编码的音频数据
 */
export const recognizeVoice = async (audioData) => {
  return apiClient.post('/voice/recognize', { audio_data: audioData });
};

export const stopRecognizeVoice = async () => {
  return apiClient.post('/voice/recognize/stop');
};

// 语音输出
export const startTTS = async () => {
  return apiClient.post('/voice/speak/start');
};

export const stopTTS = async () => {
  return apiClient.post('/voice/speak/stop');
}

/**
 * 语音合成
 * @param {string} text 文本内容
 * @param {string} roleId 角色ID
 * @param {boolean} autoPlay 是否自动播放
 */
export const synthesizeSpeech = async (text, roleId, autoPlay = true) => {
  const response = await apiClient.post('/voice/speak', { 
    text, 
    role_id: roleId 
  });
  
  if (autoPlay && response.audio_urls && response.audio_urls.length > 0) {
    // 自动播放返回的音频
    playAudioSequentially(response.audio_urls);
  }
  
  return response;
};

/**
 * 中断当前AI语音
 */
export const interruptAI = async () => {
  return apiClient.post('/interrupt');
};

/**
 * 直接与Python配置模型对话 - 使用直接API
 * @param {string} text 文本内容
 * @param {boolean} stream 是否使用流式响应
 */
export const directChatWithModel = async (text, stream = false) => {
  // 创建一个特定的axios实例用于直接模型API
  const directClient = axios.create({
    baseURL: directModelUrl,
    timeout: apiTimeout * 1.5, // 给直接模型更长的超时时间
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  });
  
  try {
    const response = await directClient.post('/direct-chat', { 
      text, 
      stream,
      voice: 'longxiang' // 默认使用龙翔声音
    });
    return response.data;
  } catch (error) {
    console.error('直接模型API调用失败:', error);
    throw error;
  }
};

/**
 * 直接与Python配置模型进行语音识别
 * @param {string} audioData Base64编码的音频数据
 */
export const directRecognizeVoice = async (audioData) => {
  const directClient = axios.create({
    baseURL: directModelUrl,
    timeout: apiTimeout * 1.5,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  });
  
  return directClient.post('/direct-voice-recognize', { audio_data: audioData });
};

export default {
  getSystemStatus,
  getRoles,
  setRole,
  sendChatMessage,
  recognizeVoice,
  synthesizeSpeech,
  interruptAI,
  // 音频处理
  playAudio,
  playAudioSequentially,
  // 直接模型API
  directChatWithModel,
  directRecognizeVoice
};
