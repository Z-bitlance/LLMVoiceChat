<template>
  <div class="voice-control-panel">
    <div class="voice-buttons">
      <button 
        @click="startRecording" 
        :disabled="isRecording || isLoading || isDisabled"
        class="voice-btn"
      >
        <span class="icon">🎤</span> 开始录音
      </button>
      <button 
        @click="stopRecording" 
        :disabled="!isRecording"
        class="voice-btn danger"
      >
        <span class="icon">⏹</span> 停止录音
      </button>
    </div>
    
    <div class="voice-feedback">
      <audio-waveform :is-active="isRecording" v-if="isRecording" />
      <div v-else-if="isProcessing" class="processing-indicator">
        <div class="loading-spinner small"></div> 正在处理语音...
      </div>
      <div v-else-if="recognizedText" class="recognized-text">
        <strong>识别结果:</strong> {{ recognizedText }}
      </div>
      <div v-else class="voice-tip">
        <span class="tip-icon">💡</span>
        <span class="tip-text">点击"开始录音"按钮，开始语音输入</span>
      </div>
    </div>
  </div>
</template>

<script>
import AudioWaveform from './AudioWaveform.vue';

export default {
  name: 'VoiceControl',
  components: {
    AudioWaveform,
  },
  props: {
    recognizedText: {
      type: String,
      default: ''
    },
    isRecording: {
      type: Boolean,
      default: false
    },
    isProcessing: {
      type: Boolean,
      default: false
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    isDisabled: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    startRecording() {
      if (this.isRecording || this.isLoading || this.isDisabled) return;
      this.$emit('start-recording');
    },
    
    stopRecording() {
      if (!this.isRecording) return;
      this.$emit('stop-recording');
    }
  }
};
</script>

<style>
.voice-control-panel {
  background-color: var(--card-bg-color);
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow-color);
  position: relative;
  transition: background-color var(--transition-speed), box-shadow var(--transition-speed);
}

.voice-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 15px;
}

.voice-btn {
  padding: 10px 20px;
  display: inline-flex;
  align-items: center;
  border-radius: 8px;
  transition: background-color 0.3s, transform 0.2s;
  font-weight: 500;
}

.voice-btn:not(:disabled):hover {
  transform: translateY(-2px);
}

.voice-btn:not(:disabled):active {
  transform: translateY(1px);
}

.voice-btn.danger {
  background-color: var(--danger-color);
}

.voice-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.icon {
  margin-right: 8px;
  font-size: 18px;
}

.voice-feedback {
  min-height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.processing-indicator, .recognized-text, .voice-tip {
  padding: 10px;
  border-radius: 8px;
  width: 100%;
  text-align: center;
}

.processing-indicator {
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
}

.recognized-text {
  background-color: rgba(64, 158, 255, 0.1);
  color: var(--text-regular);
  padding: 10px 15px;
  border-radius: 8px;
  transition: background-color var(--transition-speed), color var(--transition-speed);
}

.voice-tip {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0.8;
}

.tip-icon {
  font-size: 20px;
}

[data-theme="dark"] .recognized-text {
  background-color: rgba(64, 158, 255, 0.2);
}

@media (max-width: 768px) {
  .voice-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .voice-btn {
    width: 100%;
    max-width: 200px;
    justify-content: center;
  }
}
</style>
