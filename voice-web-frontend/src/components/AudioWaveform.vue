<template>
  <div class="audio-waveform" :class="{ active: isActive }">
    <div class="bar" v-for="(bar, index) in bars" :key="index" :style="{ height: `${bar}%` }"></div>
  </div>
</template>

<script>
export default {
  name: 'AudioWaveform',
  props: {
    isActive: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      bars: Array(15).fill(20),
      animationInterval: null
    };
  },
  watch: {
    isActive(newValue) {
      if (newValue) {
        this.startAnimation();
      } else {
        this.stopAnimation();
      }
    }
  },
  methods: {
    startAnimation() {
      if (this.animationInterval) {
        clearInterval(this.animationInterval);
      }
      
      this.animationInterval = setInterval(() => {
        // 更新波形高度
        this.bars = this.bars.map(() => {
          return this.isActive ? Math.floor(Math.random() * 80) + 20 : 20;
        });
      }, 150);
    },
    
    stopAnimation() {
      if (this.animationInterval) {
        clearInterval(this.animationInterval);
        this.animationInterval = null;
      }
      
      // 重置所有条高度
      this.bars = Array(15).fill(20);
    }
  },
  beforeUnmount() {
    this.stopAnimation();
  }
};
</script>

<style>
.audio-waveform {
  display: flex;
  align-items: center;
  height: 50px;
  gap: 2px;
  padding: 0 10px;
}

.audio-waveform .bar {
  flex: 1;
  background-color: #e0e0e0;
  border-radius: 2px;
  height: 20%;
  max-width: 4px;
  transition: height 0.2s ease;
}

.audio-waveform.active .bar {
  background-color: var(--primary-color);
}

@media (max-width: 768px) {
  .audio-waveform {
    height: 40px;
  }
  
  .audio-waveform .bar {
  max-width: 3px;
  }
}


</style>
