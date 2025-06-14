<template>
  <div class="theme-switcher">
    <button 
      @click="toggleTheme" 
      class="theme-button"
      :title="isDarkMode ? '切换到亮色主题' : '切换到暗色主题'"
    >
      <span v-if="isDarkMode">🌞</span>
      <span v-else>🌙</span>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ThemeSwitcher',
  data() {
    return {
      isDarkMode: false
    };
  },
  mounted() {
    // 检查本地存储中的主题设置
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      this.isDarkMode = true;
      this.applyTheme('dark');
    } else if (savedTheme === 'light') {
      this.isDarkMode = false;
      this.applyTheme('light');
    } else {
      // 检查系统默认主题
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.isDarkMode = true;
        this.applyTheme('dark');
      } else {
        this.isDarkMode = false;
        this.applyTheme('light');
      }
    }
  },
  methods: {
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode;
      const newTheme = this.isDarkMode ? 'dark' : 'light';
      
      this.applyTheme(newTheme);
      localStorage.setItem('theme', newTheme);
    },
    
    applyTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
    }
  }
};
</script>

<style>
.theme-switcher {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 100;
}

.theme-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s, background-color 0.3s;
}

.theme-button:hover {
  transform: scale(1.1);
}
</style>
