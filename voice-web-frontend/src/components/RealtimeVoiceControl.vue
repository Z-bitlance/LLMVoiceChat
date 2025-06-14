<template>
  <div class="voice-control">
    <div class="control-buttons">
      <!-- 麦克风按钮 -->
      <button 
        class="mic-button" 
        :class="{ active: isRecording, disabled: isDisabled }"
        @click="toggleRecording"
        :disabled="isDisabled"
      >
        <span v-if="isRecording">
          <i class="fas fa-microphone-alt"></i> 停止录音
        </span>
        <span v-else>
          <i class="fas fa-microphone"></i> 开始录音
        </span>
      </button>

      <!-- 打断按钮 -->
      <button 
        class="interrupt-button" 
        @click="handleInterrupt"
        v-if="showInterruptButton"
      >
        <i class="fas fa-hand-paper"></i> 打断AI
      </button>
    </div>

    <!-- 语音识别状态 -->
    <div class="voice-status" v-if="isRecording || isProcessing">
      <div v-if="isRecording" class="recording-status">
        <span class="recording-indicator"></span> 正在录音...
      </div>
      <div v-else-if="isProcessing" class="processing-status">
        <span class="processing-indicator"></span> 处理中...
      </div>
    </div>

    <!-- 实时语音反馈 -->
    <div class="real-time-feedback" v-if="recognizedText">
      <p>{{ recognizedText }}</p>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { realTimeRecognizeVoice, interruptAI } from '../services/api_asr';

export default {
  name: 'RealtimeVoiceControl',
  props: {
    disabled: {
      type: Boolean,
      default: false
    },
    aiSpeaking: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['start-recording', 'stop-recording', 'text-recognized', 'interrupt'],

  setup(props, { emit }) {
    const isRecording = ref(false);
    const isProcessing = ref(false);
    const mediaRecorder = ref(null);
    const audioChunks = ref([]);
    const recognizedText = ref('');
    const audioContext = ref(null);
    const analyser = ref(null);
    const microphoneStream = ref(null);
    const recordingInterval = ref(null);
    
    // 计算属性
    const isDisabled = computed(() => props.disabled);
    const showInterruptButton = computed(() => props.aiSpeaking);

    // 切换录音状态
    const toggleRecording = async () => {
      if (isRecording.value) {
        stopRecording();
      } else {
        startRecording();
      }
    };
    
    // 开始录音
    const startRecording = async () => {
      if (isRecording.value || isDisabled.value) return;
      
      try {
        recognizedText.value = '';
        audioChunks.value = [];
        
        // 请求麦克风权限
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        microphoneStream.value = stream;
        
        // 创建MediaRecorder实例
        mediaRecorder.value = new MediaRecorder(stream);
        
        // 设置音频分析器
        setupAudioAnalyser(stream);
        
        // 监听数据可用事件
        mediaRecorder.value.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.value.push(event.data);
          }
        };
        
        // 监听停止事件
        mediaRecorder.value.onstop = () => {
          processRecording();
        };
        
        // 每500毫秒发送一次数据
        mediaRecorder.value.start(500);
        
        // 设置定时发送处理
        recordingInterval.value = setInterval(() => {
          if (audioChunks.value.length > 0) {
            const tempChunks = [...audioChunks.value];
            audioChunks.value = [];
            
            // 处理音频数据
            processBatch(tempChunks);
          }
        }, 600);
        
        isRecording.value = true;
        emit('start-recording');
      } catch (error) {
        console.error('启动录音失败:', error);
        alert('无法访问麦克风，请检查浏览器权限设置。');
      }
    };
    
    // 停止录音
    const stopRecording = () => {
      if (!isRecording.value || !mediaRecorder.value) return;
      
      clearInterval(recordingInterval.value);
      mediaRecorder.value.stop();
      
      // 停止所有轨道
      if (microphoneStream.value) {
        microphoneStream.value.getTracks().forEach(track => track.stop());
      }
      
      isRecording.value = false;
      emit('stop-recording');
    };
    
    // 设置音频分析器
    const setupAudioAnalyser = (stream) => {
      try {
        audioContext.value = new (window.AudioContext || window.webkitAudioContext)();
        analyser.value = audioContext.value.createAnalyser();
        const source = audioContext.value.createMediaStreamSource(stream);
        source.connect(analyser.value);
        
        // 设置分析器参数
        analyser.value.fftSize = 256;
        analyser.value.smoothingTimeConstant = 0.8;
      } catch (error) {
        console.error('设置音频分析器失败:', error);
      }
    };
    
    // 处理一批音频数据
    const processBatch = async (chunks) => {
      try {
        if (chunks.length === 0) return;
        
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        
        reader.onloadend = async () => {
          const base64Audio = reader.result.split(',')[1];
          
          try {
            const result = await realTimeRecognizeVoice(base64Audio);
            if (result && result.recognized_text) {
              recognizedText.value = result.recognized_text;
            }
          } catch (error) {
            console.error('实时语音识别失败:', error);
          }
        };
      } catch (error) {
        console.error('处理音频批次失败:', error);
      }
    };
    
    // 处理完整录音
    const processRecording = async () => {
      if (audioChunks.value.length === 0) return;
      
      isProcessing.value = true;
      
      try {
        const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        
        reader.onloadend = async () => {
          const base64Audio = reader.result.split(',')[1];
          
          try {
            const result = await realTimeRecognizeVoice(base64Audio);
            if (result && result.recognized_text) {
              recognizedText.value = result.recognized_text;
              emit('text-recognized', result.recognized_text);
            }
          } catch (error) {
            console.error('语音识别失败:', error);
          } finally {
            isProcessing.value = false;
          }
        };
      } catch (error) {
        console.error('处理录音失败:', error);
        isProcessing.value = false;
      }
    };
    
    // 处理打断
    const handleInterrupt = async () => {
      try {
        await interruptAI();
        emit('interrupt');
      } catch (error) {
        console.error('打断AI失败:', error);
      }
    };
    
    return {
      isRecording,
      isProcessing,
      isDisabled,
      showInterruptButton,
      recognizedText,
      toggleRecording,
      handleInterrupt
    };
  }
};
</script>

<style scoped>
.voice-control {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 1rem 0;
}

.control-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.mic-button, .interrupt-button {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.mic-button {
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  color: #333;
}

.mic-button.active {
  background-color: #e74c3c;
  color: white;
  border-color: #c0392b;
}

.mic-button.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.interrupt-button {
  background-color: #3498db;
  color: white;
  border: 1px solid #2980b9;
}

.interrupt-button:hover {
  background-color: #2980b9;
}

.voice-status {
  margin-top: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}

.recording-status {
  color: #e74c3c;
  display: flex;
  align-items: center;
}

.processing-status {
  color: #3498db;
  display: flex;
  align-items: center;
}

.recording-indicator, .processing-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.recording-indicator {
  background-color: #e74c3c;
  animation: pulse 1s infinite;
}

.processing-indicator {
  background-color: #3498db;
  animation: pulse 1.5s infinite;
}

.real-time-feedback {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  width: 100%;
  text-align: center;
  font-size: 0.9rem;
  color: #495057;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}
</style>
