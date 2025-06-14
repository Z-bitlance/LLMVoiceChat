# AI语音聊天角色扮演系统 - 前端

这是AI语音聊天角色扮演系统的前端部分，使用Vue 3和Vite构建。该系统允许用户与不同角色的AI进行文字和语音对话。

## 功能特点

- 多角色选择：支持多种AI角色供用户选择
- 文本聊天：发送文字消息与AI对话
- 语音输入：支持录音并转换为文字与AI对话
- 语音输出：AI回复会通过语音合成播放
- 聊天历史：保存聊天记录并支持导出
- 暗色模式：支持明暗主题切换
- 响应式设计：适配各种屏幕尺寸

## 开发环境准备

确保您已安装：
- Node.js (推荐v16+)
- npm或yarn

## 安装与运行

1. 克隆仓库
```bash
git clone <repository-url>
cd voice-web-frontend
```

2. 安装依赖
```bash
npm install
# 或
yarn
```

3. 启动开发服务器
```bash
npm run dev
# 或
yarn dev
```

4. 构建生产版本
```bash
npm run build:prod
# 或
yarn build:prod
```

## 配置

- `.env`：开发环境配置
- `.env.production`：生产环境配置

## API接口

前端通过以下接口与后端通信：

- `/api/roles`：获取可用角色列表
- `/api/role/set`：设置当前角色
- `/api/chat`：发送聊天消息
- `/api/voice/recognize`：语音识别
- `/api/voice/speak`：语音合成

## 项目结构

```
voice-web-frontend/
├── public/              # 静态资源
├── src/                 # 源代码
│   ├── assets/          # 样式和资源
│   ├── components/      # Vue组件
│   ├── services/        # API服务
│   ├── App.vue          # 主应用组件
│   └── main.js          # 入口文件
├── index.html           # HTML模板
├── package.json         # 依赖和脚本
└── vite.config.js       # Vite配置
```

## 技术栈

- Vue 3：前端框架
- Vite：构建工具
- Axios：HTTP客户端
