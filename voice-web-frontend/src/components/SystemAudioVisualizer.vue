<template>
  <div class="system-audio-visualizer" ref="visualizerContainer">
    <div class="controls" v-if="showControls">
      <button @click="toggleListening" :class="{ active: isListening }">
        {{ isListening ? '停止监听' : '开始监听' }}
      </button>
    </div>
    <div v-if="errorMessage" class="error-message">
      <span class="error-icon">⚠️</span>
      <span>{{ errorMessage }}</span>
      <button class="error-close" @click="dismissError">×</button>
    </div>
    <div class="visualizer-container">
      <canvas ref="visualizerCanvas" class="visualizer-canvas"></canvas>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SystemAudioVisualizer',
  
  props: {
    // 是否自动开始监听
    autoStart: {
      type: Boolean,
      default: false
    },
    // 是否显示控制按钮
    showControls: {
      type: Boolean,
      default: true
    },
    // 波形颜色
    color: {
      type: String,
      default: '#2196F3'
    },
    // 波形背景色
    backgroundColor: {
      type: String,
      default: 'transparent'
    },
    // 波形高度
    height: {
      type: [Number, String],
      default: 100
    },
    // 波形显示类型: 'waveform' 或 'bars'
    visualType: {
      type: String,
      default: 'waveform',
      validator: (value) => ['waveform', 'bars'].includes(value)
    }
  },
    data() {
    return {
      isListening: false,
      audioContext: null,
      analyser: null,
      dataArray: null,
      source: null,
      rafId: null,
      canvasCtx: null,
      canvasWidth: 0,
      canvasHeight: 0,
      errorMessage: '',
    };
  },
  
  mounted() {
    this.setupCanvas();
    
    if (this.autoStart) {
      this.startListening();
    }
    
    window.addEventListener('resize', this.handleResize);
  },
  
  beforeUnmount() {
    this.stopListening();
    window.removeEventListener('resize', this.handleResize);
  },
  
  methods: {
    setupCanvas() {
      const canvas = this.$refs.visualizerCanvas;
      this.canvasCtx = canvas.getContext('2d');
      
      // 设置canvas大小
      this.handleResize();
    },
    
    handleResize() {
      const canvas = this.$refs.visualizerCanvas;
      const container = this.$refs.visualizerContainer;
      
      if (canvas && container) {
        this.canvasWidth = container.clientWidth;
        this.canvasHeight = typeof this.height === 'number' ? this.height : parseInt(this.height);
        
        canvas.width = this.canvasWidth;
        canvas.height = this.canvasHeight;
      }
    },
    
    toggleListening() {
      if (this.isListening) {
        this.stopListening();
      } else {
        this.startListening();
      }
    },
      async startListening() {
      try {
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 2048;
            // 为了获取系统音频，我们需要用户授予媒体捕获权限
          // 使用更兼容的配置，不同浏览器支持程度不同
          const stream = await navigator.mediaDevices.getDisplayMedia({ 
            video: { 
              displaySurface: 'browser',
              width: { ideal: 1 },
              height: { ideal: 1 },
              frameRate: { ideal: 1 }
            },
            audio: true,
            selfBrowserSurface: "include" // 替代 preferCurrentTab，支持更多浏览器
          });
          
          this.source = this.audioContext.createMediaStreamSource(stream);
          this.source.connect(this.analyser);
          
          // 创建缓冲区来接收音频数据
          this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
          
          // 开始可视化
          this.isListening = true;
          this.draw();
          
          // 发出事件通知父组件
          this.$emit('start-listening');
          
          // 设置停止监听的处理程序
          stream.getAudioTracks()[0].onended = () => {
            this.stopListening();
          };
        }      } catch (error) {
        console.error('启动系统音频监听失败:', error);
        
        // 根据错误类型提供不同的提示信息
        if (error.name === 'NotSupportedError') {
          this.errorMessage = '您的浏览器不支持系统音频捕获功能。请尝试使用 Chrome 或 Edge 最新版本。';
          this.$emit('error', {
            type: 'not-supported',
            message: this.errorMessage
          });
        } else if (error.name === 'NotAllowedError') {
          this.errorMessage = '您拒绝了音频捕获权限请求。请在浏览器设置中允许访问音频。';
          this.$emit('error', {
            type: 'permission-denied',
            message: this.errorMessage
          });
        } else if (error.name === 'AbortError') {
          this.errorMessage = '音频捕获请求被中断。';
          this.$emit('error', {
            type: 'aborted',
            message: this.errorMessage
          });
        } else {
          this.errorMessage = '无法访问系统音频，错误: ' + error.message;
          this.$emit('error', {
            type: 'unknown',
            message: this.errorMessage
          });
        }
      }
    },
    
    stopListening() {
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
      
      if (this.source) {
        this.source.disconnect();
        this.source = null;
      }
      
      if (this.audioContext) {
        // 在某些浏览器中，我们可以关闭 AudioContext
        if (this.audioContext.state !== 'closed' && typeof this.audioContext.close === 'function') {
          this.audioContext.close();
        }
        this.audioContext = null;
      }
      
      this.isListening = false;
      
      // 清空画布
      if (this.canvasCtx) {
        this.canvasCtx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
      }
      
      // 发出事件通知父组件
      this.$emit('stop-listening');
    },
    
    draw() {
      if (!this.isListening) return;
      
      this.rafId = requestAnimationFrame(this.draw.bind(this));
      
      this.analyser.getByteTimeDomainData(this.dataArray);
      
      // 清空画布
      this.canvasCtx.fillStyle = this.backgroundColor;
      this.canvasCtx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);
      
      if (this.visualType === 'waveform') {
        this.drawWaveform();
      } else if (this.visualType === 'bars') {
        this.drawBars();
      }
    },
    
    drawWaveform() {
      this.canvasCtx.lineWidth = 2;
      this.canvasCtx.strokeStyle = this.color;
      this.canvasCtx.beginPath();
      
      const sliceWidth = this.canvasWidth / this.analyser.frequencyBinCount;
      let x = 0;
      
      for (let i = 0; i < this.analyser.frequencyBinCount; i++) {
        const v = this.dataArray[i] / 128.0;
        const y = (v * this.canvasHeight) / 2;
        
        if (i === 0) {
          this.canvasCtx.moveTo(x, y);
        } else {
          this.canvasCtx.lineTo(x, y);
        }
        
        x += sliceWidth;
      }
      
      this.canvasCtx.lineTo(this.canvasWidth, this.canvasHeight / 2);
      this.canvasCtx.stroke();
    },
    
    drawBars() {
      const bufferLength = this.analyser.frequencyBinCount;
      
      // 获取频率数据而不是时域数据
      const dataArray = new Uint8Array(bufferLength);
      this.analyser.getByteFrequencyData(dataArray);
      
      const barWidth = this.canvasWidth / 60;
      let x = 0;
      
      for (let i = 0; i < 60; i++) {
        // 使用对数分布更均匀地显示频率范围
        const barIndex = Math.floor(Math.pow(i / 60, 2) * bufferLength);
        const barHeight = (dataArray[barIndex] / 255) * this.canvasHeight;
        
        this.canvasCtx.fillStyle = this.color;
        this.canvasCtx.fillRect(
          x, 
          this.canvasHeight - barHeight, 
          barWidth - 2, 
          barHeight
        );
        
        x += barWidth;
      }
    }
  }
};
</script>

<style scoped>
.system-audio-visualizer {
  width: 100%;
  margin: 0 auto;
  border-radius: 8px;
  overflow: hidden;
}

.controls {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.controls button {
  background-color: #f0f0f0;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.controls button:hover {
  background-color: #e0e0e0;
}

.controls button.active {
  background-color: var(--primary-color, #2196F3);
  color: white;
}

.visualizer-container {
  position: relative;
  width: 100%;
}

.visualizer-canvas {
  width: 100%;
  display: block;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .controls button {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
