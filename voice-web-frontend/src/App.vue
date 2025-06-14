<template>
  <div class="app-wrapper">
    <header class="app-header">
      <div class="container">
        <h1>AI角色扮演语音对话系统</h1>
      </div>
    </header>
    
    <main class="app-content">
      <div class="container">
        <!-- 错误通知 -->
        <div v-if="error" class="error-notification">
          <div class="error-content">
            <span class="error-icon">⚠️</span>
            <span>{{ error }}</span>
          </div>
          <button class="error-close" @click="error = null">×</button>
        </div>
        
        <div class="role-selection">
          <h2>选择角色</h2>
          <div class="role-cards" :class="{ 'loading': isRolesLoading }">
            <div 
              v-for="role in roles" 
              :key="role.id" 
              class="role-card" 
              :class="{active: selectedRole.id === role.id, 'direct-model': role.isDirect}"
              @click="selectRole(role)"
            >
              <div class="role-avatar" :style="getRoleAvatarStyle(role)">
                <template v-if="!role.avatar">{{ role.name.charAt(0) }}</template>
              </div>
              <div class="role-name">{{ role.name }}</div>
            </div>
            <div v-if="isRolesLoading" class="loading-overlay">
              <div class="loading-spinner"></div>
              <span>加载角色中...</span>
            </div>
          </div>
        </div>
        
        <div class="chat-container">
          <div class="chat-header">
            <h3>
              <span class="role-indicator" :style="getRoleAvatarStyle(selectedRole)">
                <template v-if="!selectedRole.avatar">{{ selectedRole.name.charAt(0) }}</template>
              </span>
              与 {{ selectedRole.name }} 对话中
            </h3>
            <div class="chat-actions">
              <export-chat :messages="messages" :selected-role="selectedRole" />
              <button class="clear-btn" @click="clearHistory" title="清除对话历史">
                <span>🗑️</span>
              </button>
            </div>
          </div>
          
          <div class="chat-messages" ref="messagesContainer">
            <div v-if="messages.length === 0" class="empty-message">
              <p>开始和AI对话吧！可以通过文字输入或语音输入。</p>
            </div>
            
            <chat-message 
              v-for="(message, index) in messages" 
              :key="index"
              :text="message.text"
              :isUser="message.isUser"
              :isError="message.isError"
              :time="message.time"
              :roleName="selectedRole.name"
              :roleColor="roleColors[selectedRole.id] || '#409EFF'"
              :avatar="roleAvatars[selectedRole.id]"
            />
            
            <div v-if="isResponseLoading" class="message ai-message loading-message">
              <div class="message-avatar" :style="getRoleAvatarStyle(selectedRole)">
                <template v-if="!selectedRole.avatar">{{ selectedRole.name.charAt(0) }}</template>
              </div>
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
            <div class="chat-input">

            
              <input 
                v-model="inputText" 
                placeholder="请输入消息..." 
                @keyup.enter="sendTextMessage"
                :disabled="isResponseLoading"
              />
              <button @click="sendTextMessage" :disabled="!inputText.trim() || isResponseLoading">发送</button>
              <button 
                class="interrupt-button" 
                @click="handleInterrupt" 
                v-if="isPlaying"
                title="中断AI语音"
              >
                <span class="interrupt-icon">⏹</span>
              </button>
            
          </div>
        </div>
          <voice-control
          :isRecording="isRecording"
          :isProcessing="isVoiceProcessing"
          :isLoading="isResponseLoading"
          :recognizedText="recognizedText"
          @start-recording="startRecording"
          @stop-recording="stopRecording"
        />
        
        <div class="system-audio-section">
          <h3>系统音频可视化</h3>
          <system-audio-visualizer
            :autoStart="false"
            :showControls="true"
            :height="80"
            visualType="bars"
            color="var(--primary-color)"
          />
        </div>
      </div>
    </main>
    
    <ThemeSwitcher />
    
    <footer class="app-footer">
      <div class="container">
        <p>© {{ new Date().getFullYear() }} AI对话系统</p>
      </div>
    </footer>
  </div>
</template>

<script>
// 导入更新版API
import { 
  getRoles, sendChatMessage, recognizeVoice, synthesizeSpeech, 
  setRole, directChatWithModel, directRecognizeVoice, interruptAI 
} from './services/api_updated';
import AudioWaveform from './components/AudioWaveform.vue';
import ThemeSwitcher from './components/ThemeSwitcher.vue';
import ExportChat from './components/ExportChat.vue';
import ChatMessage from './components/ChatMessage.vue';
import VoiceControl from './components/VoiceControl.vue';
import SystemAudioVisualizer from './components/SystemAudioVisualizer.vue';

export default {
  components: {
    AudioWaveform,
    ThemeSwitcher,
    ExportChat,
    ChatMessage,
    VoiceControl,
    SystemAudioVisualizer,
  },  data() {
    return {
      // 角色列表
      roles: [],
      // 选中的角色
      selectedRole: { id: 'assistant', name: 'AI助手', voice: 'longxiang' },
      // 消息列表
      messages: [],
      // 输入文本
      inputText: '',
      // 录音状态
      isRecording: false,
      // 语音识别结果
      recognizedText: '',
      // 媒体录音器
      mediaRecorder: null,
      // 音频数据
      audioChunks: [],
      // 加载状态
      isRolesLoading: false,
      isResponseLoading: false,
      isVoiceProcessing: false,
      // 错误状态
      error: null,
      // 当前会话ID
      sessionId: null,      // 角色头像颜色映射
      roleColors: {
        'assistant': '#409EFF',
        'teacher': '#67C23A',
        'doctor': '#E6A23C',
        'customer_service': '#F56C6C',
        'direct_model': '#8A2BE2', // 直接模型角色使用紫色
      },
      // 角色头像URL映射（为空时使用首字母）
      roleAvatars: {
        // 如果有头像图片，可以在这里设置URL
        // 'assistant': '/path/to/avatar.png',
      },
      // 正在播放音频
      isPlaying: false,
    };
  },
  
  mounted() {
    // 加载角色列表
    this.loadRoles();
    
    // 从本地存储恢复对话历史
    this.loadChatHistory();
    
    // 生成新的会话ID
    this.sessionId = this.generateSessionId();
    
    // 添加窗口关闭前保存对话历史的事件监听器
    window.addEventListener('beforeunload', this.saveChatHistory);
  },
  
  beforeDestroy() {
    // 移除事件监听器
    window.removeEventListener('beforeunload', this.saveChatHistory);
  },
  
  methods: {
    // 生成会话ID
    generateSessionId() {
      return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    },
    
    // 保存对话历史到本地存储
    saveChatHistory() {
      try {
        // 只保存最近的50条消息
        const recentMessages = this.messages.slice(-50);
        
        const historyData = {
          messages: recentMessages,
          selectedRole: this.selectedRole,
          sessionId: this.sessionId,
          timestamp: Date.now()
        };
        
        localStorage.setItem('chat_history', JSON.stringify(historyData));
      } catch (error) {
        console.error('保存对话历史失败:', error);
      }
    },
    
    // 从本地存储加载对话历史
    loadChatHistory() {
      try {
        const historyData = localStorage.getItem('chat_history');
        
        if (historyData) {
          const data = JSON.parse(historyData);
          
          // 检查历史记录的有效性和时间戳（24小时有效）
          const isValid = data && data.messages && 
                          data.timestamp && 
                          (Date.now() - data.timestamp < 24 * 60 * 60 * 1000);
          
          if (isValid) {
            this.messages = data.messages;
            
            // 如果历史记录中有选中的角色，使用它
            if (data.selectedRole) {
              this.selectedRole = data.selectedRole;
            }
            
            // 使用旧的会话ID
            if (data.sessionId) {
              this.sessionId = data.sessionId;
            }
            
            this.$nextTick(() => {
              this.scrollToBottom();
            });
          }
        }
      } catch (error) {
        console.error('加载对话历史失败:', error);
      }
    },
    
    // 加载角色列表
    async loadRoles() {
      if (this.isRolesLoading) return;
      
      this.isRolesLoading = true;
      this.error = null;
      
      try {
        const response = await getRoles();
        if (response && response.roles && response.roles.length > 0) {
          this.roles = response.roles;
          // 默认选中第一个角色
          this.selectRole(this.roles[0]);
        } else {
          // 如果API返回空列表，使用默认角色
          console.warn('API返回了空角色列表，使用默认角色');
          this.roles = [
            { id: 'assistant', name: 'AI助手', voice: 'longxiang' },
            { id: 'teacher', name: '教师', voice: 'xiaoyun' },
            { id: 'doctor', name: '医生', voice: 'aixia' },
            { id: 'customer_service', name: '客服', voice: 'ruoxi' },
            { id: 'direct_model', name: '直接模型', voice: 'longxiang', isDirect: true },
          ];
        }
      } catch (error) {
        console.error('加载角色列表失败:', error);
        this.error = '加载角色列表失败';
        // 使用默认角色
        this.roles = [
          { id: 'assistant', name: 'AI助手', voice: 'longxiang' },
          { id: 'teacher', name: '教师', voice: 'xiaoyun' },
          { id: 'doctor', name: '医生', voice: 'aixia' },
          { id: 'customer_service', name: '客服', voice: 'ruoxi' },
          { id: 'direct_model', name: '直接模型', voice: 'longxiang', isDirect: true },
        ];
      } finally {
        this.isRolesLoading = false;
      }
    },
      // 选择角色
    async selectRole(role) {
      // 如果选择的是同一个角色，不做任何操作
      if (this.selectedRole.id === role.id) return;
      
      this.selectedRole = role;
      console.log('已选择角色:', role);
      
      // 对于直接模型角色，不需要调用标准API
      if (role.isDirect) {
        console.log('选择了直接模型角色，跳过后端API调用');
        // 保存当前会话状态
        this.saveChatHistory();
        return;
      }
      
      // 通知后端角色选择
      try {
        await setRole(role.id);
        // 保存当前会话状态
        this.saveChatHistory();
      } catch (error) {
        console.error('设置角色失败:', error);
        this.error = '设置角色失败，请重试';
      }
    },
    
    // 发送文本消息
    async sendTextMessage() {
      const text = this.inputText.trim();
      if (!text || this.isResponseLoading) return;
      
      // 清空输入框
      this.inputText = '';
      
      // 添加用户消息
      this.addMessage(text, true);
      
      // 滚动到底部
      this.scrollToBottom();
      
      // 设置响应加载状态
      this.isResponseLoading = true;
      this.error = null;
        try {
        // 判断是否为直接模型角色
        if (this.selectedRole.isDirect) {
          console.log('使用直接模型API发送消息');
          const directResponse = await directChatWithModel(text);
          
          if (directResponse && directResponse.response) {
            // 添加AI回复
            this.addMessage(directResponse.response, false);
            
            // 滚动到底部
            this.scrollToBottom();
            
            // 直接模型会自动处理语音合成，不需要额外调用TTS API
            this.saveChatHistory();
          } else {
            console.error('无效的直接模型API响应:', directResponse);
            this.error = '收到无效的响应，请重试';
            this.addMessage('抱歉，直接模型无法处理您的请求。请重试。', false, true);
          }
          
          // 结束处理
          this.isResponseLoading = false;
          return;
        }
        
        // 调用标准后端API发送消息
        const response = await sendChatMessage(text, this.selectedRole.id);
        
        if (response && response.response) {
          // 添加AI回复
          this.addMessage(response.response, false);
          
          // 滚动到底部
          this.scrollToBottom();
          
          // 调用语音合成API
          try {
            const audioResult = await synthesizeSpeech(response.response, this.selectedRole.id);
            
            if (audioResult && audioResult.audio_paths && audioResult.audio_paths.length > 0) {
              // 播放合成的语音
              this.playAudio(audioResult.audio_paths);
            } else {
              console.warn('语音合成API未返回有效的音频路径');
            }
          } catch (audioError) {
            console.error('语音合成失败:', audioError);
            // 不显示错误给用户，因为文本响应已经显示
          } finally {
            // 保存对话历史
            this.saveChatHistory();
          }
        } else {
          console.error('无效的API响应:', response);
          this.error = '收到无效的响应，请重试';
          this.addMessage('抱歉，我无法处理您的请求。请重试或联系管理员。', false, true);
        }
      } catch (error) {
        console.error('发送消息失败:', error);
        this.error = '发送消息失败，请重试';
        // 添加错误消息到聊天窗口
        this.addMessage('消息发送失败，请重试。', false, true);
      } finally {
        // 无论成功或失败，都关闭加载状态
        this.isResponseLoading = false;
        this.scrollToBottom();
      }
    },
    
    // 添加消息到列表
    addMessage(text, isUser, isError = false) {
      const now = new Date();
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      
      this.messages.push({
        text,
        isUser,
        time,
        isError,
        sessionId: this.sessionId,
      });
    },
    
    // 滚动到消息底部
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },
    
    // 开始录音
    async startRecording() {
      if (this.isRecording || this.isResponseLoading) return;
      
      try {
        this.recognizedText = '';
        this.error = null;
        
        // 请求麦克风权限
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // 创建MediaRecorder实例
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];
        
        // 监听数据可用事件
        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data);
        };
        
        // 监听录音停止事件
        this.mediaRecorder.onstop = () => {
          // 处理录音数据
          this.processRecording();
          
          // 停止所有音轨
          stream.getTracks().forEach(track => track.stop());
        };
        
        // 开始录音
        this.mediaRecorder.start();
        this.isRecording = true;
        
        // 10秒后自动停止录音
        setTimeout(() => {
          if (this.isRecording && this.mediaRecorder) {
            this.stopRecording();
          }
        }, 10000);
      } catch (error) {
        console.error('无法访问麦克风:', error);
        this.error = '无法访问麦克风';
        alert('无法访问麦克风，请确保已授予麦克风权限。');
      }
    },
    
    // 停止录音
    stopRecording() {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop();
        this.isRecording = false;
        this.isVoiceProcessing = true;
      }
    },
      // 处理录音数据
    processRecording() {
      if (this.audioChunks.length === 0) {
        this.isVoiceProcessing = false;
        this.error = '录音失败，未捕获到音频数据';
        return;
      }
      
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
      
      // 转换为Base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      
      reader.onloadend = async () => {
        try {
          // 获取Base64编码的音频数据
          const base64Audio = reader.result.split(',')[1];
            // 调用语音识别API
          try {
            // 判断是否使用直接模型
            let result;
            if (this.selectedRole.isDirect) {
              console.log('使用直接模型API进行语音识别');
              result = await directRecognizeVoice(base64Audio);
            } else {
              result = await recognizeVoice(base64Audio);
            }
            
            if (result && result.recognized_text && result.recognized_text.trim()) {
              this.recognizedText = result.recognized_text;
              
              // 将识别结果填入输入框
              this.inputText = this.recognizedText;
              
              // 自动发送消息
              this.sendTextMessage();
            } else {
              console.error('语音识别API没有返回有效结果');
              this.error = '语音识别失败';
              this.recognizedText = '无法识别语音，请重试';
            }
          } catch (apiError) {
            console.error('语音识别API调用失败:', apiError);
            this.error = '语音识别API调用失败';
            this.recognizedText = '语音识别失败，请重试';
          }
        } catch (error) {
          console.error('处理录音失败:', error);
          this.error = '处理录音失败';
          this.recognizedText = '处理录音失败，请重试';
        } finally {
          this.isVoiceProcessing = false;
        }
      };
      
      reader.onerror = () => {
        console.error('读取录音文件失败');
        this.error = '读取录音文件失败';
        this.isVoiceProcessing = false;
        this.recognizedText = '处理录音失败，请重试';
      };
    },

    // 播放音频
    playAudio(audioPaths) {
      if (!audioPaths || audioPaths.length === 0) return;

      // 顺序播放多个音频文件
      this.playAudioSequentially(audioPaths);
    },
    
    // 处理中断AI语音
    async handleInterrupt() {
      try {
        this.isPlaying = false;
        // 调用后端API中断当前语音
        await interruptAI();
        console.log('已中断AI语音');
      } catch (error) {
        console.error('中断AI语音失败:', error);
      }
    },
    
    // 播放单个音频文件
    playSingleAudio(audioPath) {
      return new Promise((resolve, reject) => {
        // 设置正在播放状态
        this.isPlaying = true;
        
        // 创建音频元素
        const audio = new Audio();
        
        // 设置音频源（完整URL）
        // 如果路径是相对路径，需要添加baseURL
        if (audioPath.startsWith('http')) {
          audio.src = audioPath;
        } else {
          // 假设后端API和前端在同一个域名下
          const baseUrl = window.location.origin;
          audio.src = `${baseUrl}${audioPath.startsWith('/') ? '' : '/'}${audioPath}`;
        }
        
        // 添加事件监听器
        audio.onplay = () => {
          console.log(`开始播放音频: ${audioPath}`);
        };
        
        audio.onended = () => {
          console.log(`音频播放结束: ${audioPath}`);
          resolve();
        };
        
        audio.onerror = (error) => {
          console.error(`音频播放错误: ${audioPath}`, error);
          this.error = '音频播放失败';
          this.isPlaying = false;
          reject(error);
        };
        
        // 播放音频
        audio.play().catch(error => {
          console.error(`音频播放失败: ${audioPath}`, error);
          this.error = '音频播放失败';
          this.isPlaying = false;
          reject(error);
        });
      });
    },
    
    // 顺序播放多个音频文件
    async playAudioSequentially(audioPaths) {
      for (const audioPath of audioPaths) {
        try {
          // 如果中断了播放，则退出循环
          if (!this.isPlaying) {
            break;
          }
          await this.playSingleAudio(audioPath);
        } catch (error) {
          console.error(`播放音频失败: ${audioPath}`, error);
          // 继续播放下一个音频
        }
      }
      // 播放完成后重置状态
      this.isPlaying = false;
    },
    
    // 清除会话历史
    clearHistory() {
      if (confirm('确定要清除所有对话历史吗？这将无法恢复。')) {
        this.messages = [];
        this.sessionId = this.generateSessionId();
        localStorage.removeItem('chat_history');
      }
    },
    
    // 获取角色头像的样式
    getRoleAvatarStyle(role) {
      if (!role) return {};
      
      // 如果有头像图片，优先使用图片
      if (this.roleAvatars[role.id]) {
        return {
          backgroundImage: `url(${this.roleAvatars[role.id]})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        };
      }
      
      // 否则使用颜色背景
      const color = this.roleColors[role.id] || '#409EFF'; // 默认蓝色
      return {
        backgroundColor: color,
      };
    },
  }
};
</script>

<style>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: var(--header-bg-color);
  color: white;
  padding: 15px 0;
  box-shadow: 0 2px 4px var(--shadow-color);
  transition: background-color var(--transition-speed);
}

.app-header h1 {
  font-size: 1.8rem;
  margin: 0;
}

.app-content {
  flex: 1;
  padding: 30px 0;
}

.app-footer {
  background-color: var(--footer-bg-color);
  padding: 15px 0;
  border-top: 1px solid var(--border-color);
  text-align: center;
  color: var(--text-secondary);
  transition: background-color var(--transition-speed), border-color var(--transition-speed);
}

.role-selection {
  margin-bottom: 30px;
  position: relative;
}

.role-selection h2 {
  font-size: 1.5rem;
  margin-bottom: 15px;
  color: var(--text-primary);
  transition: color var(--transition-speed);
}

.role-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  position: relative;
}

.role-card {
  width: 80px;
  text-align: center;
  cursor: pointer;
  padding: 10px;
  border-radius: 8px;
  transition: all 0.3s;
  border: 1px solid transparent;
  background-color: var(--card-bg-color);
  box-shadow: 0 2px 8px var(--shadow-color);
}

.role-card:hover {
  background-color: rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.role-card.active {
  background-color: rgba(64, 158, 255, 0.2);
  border: 1px solid var(--primary-color);
  transform: translateY(-3px);
  box-shadow: 0 4px 12px var(--shadow-color);
}

.role-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto 8px;
  background-size: cover;
  background-position: center;
  transition: transform 0.2s;
  box-shadow: 0 2px 6px var(--shadow-color);
}

.role-card:hover .role-avatar {
  transform: scale(1.05);
}

.role-card.active .role-avatar {
  transform: scale(1.1);
}

.role-name {
  font-size: 14px;
  color: var(--text-primary);
  transition: color var(--transition-speed);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-container {
  height: 450px;
  display: flex;
  flex-direction: column;
  background-color: var(--chat-bg-color);
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow-color);
  margin-bottom: 20px;
  position: relative;
  transition: background-color var(--transition-speed), box-shadow var(--transition-speed);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid var(--border-color);
  transition: border-color var(--transition-speed);
  background-color: rgba(64, 158, 255, 0.05);
}

.chat-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 500;
  display: flex;
  align-items: center;
  transition: color var(--transition-speed);
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.role-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  margin-right: 8px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  scroll-behavior: smooth;
}

.empty-message {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: color var(--transition-speed);
}

.empty-message p {
  margin-top: 10px;
  text-align: center;
  max-width: 300px;
}

.empty-message:before {
  content: '💬';
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

.chat-input {
  display: flex;
  padding: 12px 15px;
  border-top: 1px solid var(--border-color);
  transition: border-color var(--transition-speed);
  background-color: rgba(255, 255, 255, 0.05);
}

.chat-input input {
  flex: 1;
  margin-right: 10px;
  padding: 10px 15px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  background-color: var(--card-bg-color);
  color: var(--text-primary);
}

.chat-input input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.chat-input button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 20px;
}

.chat-input button:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.chat-input button:active:not(:disabled) {
  transform: translateY(1px);
}

.chat-input button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.loading-message {
  display: flex;
  height: 40px;
  margin-bottom: 15px;
  max-width: 85%;
  margin-right: auto;
  align-items: center;
}

.loading-dots {
  display: flex;
  align-items: center;
  background-color: var(--ai-msg-bg);
  padding: 10px 15px;
  border-radius: 18px;
  border-top-left-radius: 0;
}

.loading-dots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
  margin: 0 3px;
  animation: bouncingDots 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bouncingDots {
  0%, 80%, 100% { 
    transform: scale(0);
  } 40% { 
    transform: scale(1.0);
  }
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(64, 158, 255, 0.3);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spinner 1s linear infinite;
  margin-right: 8px;
}

.loading-spinner.small {
  width: 14px;
  height: 14px;
  border-width: 2px;
}

@keyframes spinner {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 8px;
  transition: background-color var(--transition-speed);
}

[data-theme="dark"] .loading-overlay {
  background-color: rgba(0, 0, 0, 0.5);
}

.error-notification {
  background-color: #fef0f0;
  border: 1px solid #fde2e2;
  color: var(--danger-color);
  padding: 10px 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color var(--transition-speed);
}

[data-theme="dark"] .error-notification {
  background-color: rgba(245, 108, 108, 0.1);
  border-color: rgba(245, 108, 108, 0.3);
}

.error-content {
  display: flex;
  align-items: center;
}

.error-icon {
  margin-right: 10px;
}

.error-close {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  padding: 0 5px;
}

.error-close:hover {
  color: var(--danger-color);
}

.clear-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 5px;
  transition: color 0.3s;
}

.clear-btn:hover {
  color: var(--danger-color);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.3rem;
  }
  
  .role-selection h2 {
    font-size: 1.2rem;
  }
  
  .role-cards {
    justify-content: center;
  }
  
  .chat-container {
    height: 400px;
  }
  
  .chat-input {
    padding: 10px;
  }
  
  .chat-input input {
    padding: 8px 12px;
  }
  
  .chat-input button {
    padding: 0 15px;
    height: 36px;
  }
  
  .role-selection, .chat-container,  .voice-control, .system-audio-section {
    margin-bottom: 15px;
  }
  
  .system-audio-section h3 {
    font-size: 1rem;
    margin-bottom: 12px;
    color: var(--text-primary);
    transition: color var(--transition-speed);
  }
}

@media (max-width: 480px) {
  .app-header h1 {
    font-size: 1.2rem;
  }
  
  .app-content {
    padding: 15px 0;
  }
  
  .chat-container {
    height: 350px;
  }
  
  .role-card {
    width: 70px;
  }
  
  .role-avatar {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .system-audio-section h3 {
    font-size: 0.9rem;
  }
}

/* 系统音频部分样式 */
.system-audio-section {
  margin-top: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 15px;
  background-color: var(--card-bg-color);
  box-shadow: 0 2px 8px var(--shadow-color);
  transition: all 0.3s ease;
}
</style>
