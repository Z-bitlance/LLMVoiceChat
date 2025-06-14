import axios from 'axios';

// 读取环境变量
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const apiTimeout = parseInt(import.meta.env.VITE_API_TIMEOUT || '20000');

// 本地后端API地址
const localBackendUrl = 'http://localhost:8000/api';

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
    
    // 如果是取消请求，不进行重试
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }
    
    // 请求已经重试过或者没有配置retries字段，直接返回错误
    if (config._retryCount === undefined) {
      config._retryCount = 0;
    }
    
    if (config._retryCount >= MAX_RETRIES) {
      return Promise.reject(error);
    }
    
    config._retryCount += 1;
    console.log(`重试请求 ${config.url} (${config._retryCount}/${MAX_RETRIES})`);
    
    // 创建延迟
    const delay = new Promise(resolve => {
      setTimeout(() => {
        resolve();
      }, retryDelay(config._retryCount));
    });
    
    // 返回一个Promise，延迟后重试请求
    await delay;
    return apiClient(config);
  }
);

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
 */
export const sendChatMessage = async (text, roleId) => {
  const response = await apiClient.post('/chat', { 
    text, 
    role_id: roleId,
    stream: false
  });
  return response;
};

/**
 * 语音识别
 * @param {string} audioData Base64编码的音频数据
 */
export const recognizeVoice = async (audioData) => {
  return apiClient.post('/voice/recognize', { audio_data: audioData });
};

/**
 * 语音合成
 * @param {string} text 合成文本
 * @param {string} roleId 角色ID
 */
export const synthesizeSpeech = async (text, roleId) => {
  return apiClient.post('/voice/speak', { 
    text, 
    role_id: roleId
  });
};

/**
 * 中断当前AI响应
 */
export const interruptAI = async () => {
  return apiClient.post('/interrupt');
};

/**
 * 播放单个音频文件
 * @param {string} audioPath 音频文件URL
 * @returns {Promise} 表示音频播放状态的Promise
 */
export const playSingleAudio = (audioPath) => {
  return new Promise((resolve, reject) => {
    // 创建音频元素
    const audio = new Audio(audioPath);
    
    // 监听事件
    audio.onended = () => {
      resolve();
    };
    
    audio.onerror = (error) => {
      console.error(`播放音频失败: ${audioPath}`, error);
      reject(error);
    };
    
    // 开始播放
    audio.play().catch(error => {
      console.error(`开始播放失败: ${audioPath}`, error);
      reject(error);
    });
  });
};

/**
 * 顺序播放多个音频文件
 * @param {Array<string>} audioPaths 音频文件URL数组
 */
export const playAudioSequentially = async (audioPaths) => {
  for (const audioPath of audioPaths) {
    try {
      await playSingleAudio(audioPath);
    } catch (error) {
      console.error(`播放音频失败: ${audioPath}`, error);
    }
  }
};

/**
 * 播放多个音频文件
 * @param {Array<string>} audioPaths 音频文件URL数组
 */
export const playAudio = async (audioPaths) => {
  return playAudioSequentially(audioPaths);
};

/**
 * 直接进行实时语音识别，并可能打断AI
 * @param {string} audioData Base64编码的音频数据
 */
export const realTimeRecognizeVoice = async (audioData) => {
  return apiClient.post('/direct-recognize', { audio_data: audioData });
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
  // 新增实时语音识别
  realTimeRecognizeVoice
};
