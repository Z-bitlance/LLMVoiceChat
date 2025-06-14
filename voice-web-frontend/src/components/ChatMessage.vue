<template>
  <div 
    class="message" 
    :class="{
      'user-message': isUser, 
      'ai-message': !isUser,
      'error-message': isError
    }"
  >
    <div class="message-avatar" v-if="!isUser" :style="avatarStyle">
      <template v-if="!avatar">{{ roleName.charAt(0) }}</template>
    </div>
    <div class="message-avatar user-avatar" v-else>👤</div>
    <div class="message-bubble">
      <div class="message-content">
        {{ text }}
      </div>
      <div class="message-time">{{ time }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatMessage',
  props: {
    text: {
      type: String,
      required: true
    },
    isUser: {
      type: Boolean,
      default: false
    },
    isError: {
      type: Boolean,
      default: false
    },
    time: {
      type: String,
      required: true
    },
    roleName: {
      type: String,
      default: 'AI'
    },
    avatar: {
      type: String,
      default: ''
    },
    roleColor: {
      type: String,
      default: '#409EFF'
    }
  },
  computed: {
    avatarStyle() {
      if (this.avatar) {
        return {
          backgroundImage: `url(${this.avatar})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        };
      }
      
      return {
        backgroundColor: this.roleColor,
      };
    }
  }
};
</script>

<style>
.message {
  display: flex;
  margin-bottom: 20px;
  max-width: 85%;
  clear: both;
  position: relative;
}

.user-message {
  margin-left: auto;
  flex-direction: row-reverse;
}

.ai-message {
  margin-right: auto;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  margin: 0 8px;
  flex-shrink: 0;
  box-shadow: 0 2px 4px var(--shadow-color);
}

.user-avatar {
  background-color: #6c757d;
}

.message-bubble {
  display: flex;
  flex-direction: column;
}

.message-content {
  padding: 10px 15px;
  border-radius: 18px;
  word-break: break-word;
}

.user-message .message-content {
  background-color: var(--user-msg-bg);
  color: white;
  border-top-right-radius: 0;
}

.ai-message .message-content {
  background-color: var(--ai-msg-bg);
  color: var(--ai-msg-text);
  border-top-left-radius: 0;
}

.message-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  transition: color var(--transition-speed);
}

.user-message .message-time {
  text-align: right;
}

.error-message .message-content {
  background-color: rgba(245, 108, 108, 0.1);
  color: var(--danger-color);
  border: 1px solid var(--danger-color);
}

[data-theme="dark"] .error-message .message-content {
  background-color: rgba(245, 108, 108, 0.2);
}
</style>
