<template>
  <div class="export-button">
    <button 
      @click="showExportOptions" 
      class="export-btn"
      title="导出对话"
    >
      📥
    </button>
    
    <div v-if="showOptions" class="export-options">
      <div class="export-header">
        <h3>导出对话历史</h3>
        <button @click="showOptions = false" class="close-btn">×</button>
      </div>
      
      <div class="export-content">
        <div class="option" @click="exportAsText">
          <span class="icon">📄</span>
          <span class="label">文本文件 (.txt)</span>
        </div>
        
        <div class="option" @click="exportAsJSON">
          <span class="icon">📊</span>
          <span class="label">JSON文件 (.json)</span>
        </div>
        
        <div class="option" @click="copyToClipboard">
          <span class="icon">📋</span>
          <span class="label">复制到剪贴板</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExportChat',
  props: {
    messages: {
      type: Array,
      required: true
    },
    selectedRole: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      showOptions: false
    };
  },
  methods: {
    showExportOptions() {
      this.showOptions = true;
    },
    
    formatMessagesAsText() {
      if (!this.messages || this.messages.length === 0) {
        return '暂无对话记录';
      }
      
      const roleName = this.selectedRole.name || 'AI';
      const header = `与${roleName}的对话记录\n日期：${new Date().toLocaleString()}\n\n`;
      
      const content = this.messages.map(msg => {
        const speaker = msg.isUser ? '我' : roleName;
        return `${speaker} (${msg.time}):\n${msg.text}\n`;
      }).join('\n');
      
      return header + content;
    },
    
    exportAsText() {
      const text = this.formatMessagesAsText();
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      this.downloadFile(blob, '对话记录.txt');
      this.showOptions = false;
    },
    
    exportAsJSON() {
      const data = {
        role: this.selectedRole,
        date: new Date().toISOString(),
        messages: this.messages
      };
      
      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: 'application/json;charset=utf-8' });
      this.downloadFile(blob, '对话记录.json');
      this.showOptions = false;
    },
    
    async copyToClipboard() {
      const text = this.formatMessagesAsText();
      
      try {
        await navigator.clipboard.writeText(text);
        alert('已复制到剪贴板');
      } catch (error) {
        console.error('复制失败:', error);
        alert('复制失败，请手动复制');
      }
      
      this.showOptions = false;
    },
    
    downloadFile(blob, filename) {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
      
      // 清理
      setTimeout(() => {
        URL.revokeObjectURL(link.href);
      }, 100);
    }
  }
};
</script>

<style>
.export-button {
  position: relative;
}

.export-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 5px 10px;
  transition: color 0.3s;
}

.export-btn:hover {
  color: var(--primary-color);
}

.export-options {
  position: absolute;
  top: 100%;
  right: 0;
  width: 200px;
  background-color: white;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.export-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid var(--border-color);
}

.export-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 0 5px;
}

.export-content {
  padding: 10px 0;
}

.option {
  padding: 8px 15px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.option:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

.option .icon {
  margin-right: 10px;
  font-size: 16px;
}

.option .label {
  font-size: 14px;
}

[data-theme="dark"] .export-options {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
}

[data-theme="dark"] .export-header {
  border-color: #3d3d3d;
}

[data-theme="dark"] .option:hover {
  background-color: rgba(64, 158, 255, 0.2);
}
</style>
