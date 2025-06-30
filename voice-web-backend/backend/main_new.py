import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys

# 添加项目根目录到系统路径
# ROOT_DIR = Path(__file__).parent
# sys.path.append(str(ROOT_DIR))

# 从新的api模块导入路由
from api.routes_new import router

# 创建FastAPI应用
app = FastAPI(
    title="语音对话系统 API",
    description="集成了实时语音识别、语音合成和大模型的对话系统API",
    version="1.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保静态文件目录存在
static_dir = Path("backend/static")
static_dir.mkdir(parents=True, exist_ok=True)

# 音频文件目录
audio_dir = static_dir / "audio"
audio_dir.mkdir(exist_ok=True)

# 日志目录
logs_dir = static_dir / "logs"
logs_dir.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 包含所有API路由
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "语音对话系统API正在运行",
        "version": "1.1.0",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时释放所有资源"""
    try:
        print("正在关闭应用并释放所有资源...")
        
        # 获取对话管理器实例
        from api.routes_new import dialogue_manager
        
        # 停止ASR服务
        if hasattr(dialogue_manager, 'asr_manager') and dialogue_manager.asr_manager:
            print("关闭ASR服务...")
            dialogue_manager.asr_manager.stop_asr()
            dialogue_manager.asr_manager = None
            
        # 停止语音服务
        if hasattr(dialogue_manager, 'voice_speak') and dialogue_manager.voice_speak:
            print("关闭语音合成服务...")
            if hasattr(dialogue_manager.voice_speak, 'interrupt_ai'):
                dialogue_manager.voice_speak.interrupt_ai()
                
            # 停止缓冲线程
            if hasattr(dialogue_manager.voice_speak, 'buffer_thread_lock'):
                with dialogue_manager.voice_speak.buffer_thread_lock:
                    dialogue_manager.voice_speak.buffer_thread_running = False
                    
            dialogue_manager.voice_speak = None
            
        # 终止运行状态
        dialogue_manager.running = False
        dialogue_manager.state = "idle"
        
        # 强制终止所有相关线程
        import threading
        current_thread = threading.current_thread()
        for thread in threading.enumerate():
            if thread is not current_thread and not thread.daemon:
                try:
                    print(f"强制终止线程: {thread.name}")
                    thread._stop()
                except:
                    pass
        
        print("所有资源已释放完毕")
    except Exception as e:
        print(f"关闭时释放资源失败: {e}")


@app.post("/shutdown")
async def shutdown_server():
    """强制关闭服务器"""
    try:
        print("接收到关闭服务器指令")
        
        # 在新线程中关闭服务器，以便能够先返回响应
        import threading
        import os
        import signal
        import time
        
        def terminate_server():
            # 确保有足够时间返回响应
            time.sleep(1)
            print("强制终止服务器进程...")
            # 发送终止信号给当前进程
            os.kill(os.getpid(), signal.SIGTERM)
        
        # 启动终止线程
        threading.Thread(target=terminate_server).start()
        
        return {"status": "success", "message": "服务器正在关闭..."}
    except Exception as e:
        return {"status": "error", "message": f"关闭服务器失败: {str(e)}"}


def cleanup_resources():
    """在程序退出前清理所有资源"""
    try:
        # 导入对话管理器
        from api.routes_new import dialogue_manager
        
        print("正在手动清理所有资源...")
        
        # 停止ASR服务
        if hasattr(dialogue_manager, 'asr_manager') and dialogue_manager.asr_manager:
            print("关闭ASR服务...")
            if hasattr(dialogue_manager.asr_manager, 'stop_asr'):
                dialogue_manager.asr_manager.stop_asr()
            dialogue_manager.asr_manager.running = False
            dialogue_manager.asr_manager = None
            
        # 停止语音服务
        if hasattr(dialogue_manager, 'voice_speak') and dialogue_manager.voice_speak:
            print("关闭语音合成服务...")
            if hasattr(dialogue_manager.voice_speak, 'interrupt_ai'):
                dialogue_manager.voice_speak.interrupt_ai()
            
            # 如果有播放器，确保停止
            if hasattr(dialogue_manager.voice_speak, 'player'):
                dialogue_manager.voice_speak.player.stop()
                
            # 停止缓冲线程
            if hasattr(dialogue_manager.voice_speak, 'buffer_thread_running'):
                dialogue_manager.voice_speak.buffer_thread_running = False
                
            dialogue_manager.voice_speak = None
            
        # 终止对话管理器
        dialogue_manager.running = False
        
        # 等待所有非守护线程结束
        import threading
        import time
        
        main_thread = threading.current_thread()
        for thread in threading.enumerate():
            if thread is not main_thread and not thread.daemon:
                print(f"等待线程结束: {thread.name}")
                thread.join(timeout=1.0)
                
        print("所有资源已清理完毕")
    except Exception as e:
        print(f"清理资源时出错: {e}")

# 注册退出处理函数
import atexit
atexit.register(cleanup_resources)

# 直接运行应用
if __name__ == "__main__":
    import signal
    
    def handle_exit(signum, frame):
        print(f"收到信号 {signum}，准备关闭服务...")
        # 此处不需要做任何事情，因为uvicorn会处理信号并调用应用的shutdown事件
        sys.exit(0)
    
    # 注册信号处理程序
    signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # 终止信号
    
    try:
        print("启动语音对话系统后端...")
        port = int(os.environ.get("PORT", 51001))
        # 禁用reload，因为它会导致进程无法正确关闭
        uvicorn.run("main_new:app", host="0.0.0.0", port=port, reload=False)
    except KeyboardInterrupt:
        print("检测到键盘中断，正在关闭服务...")
    except Exception as e:
        print(f"启动服务失败: {e}")
    finally:
        # 确保在任何情况下都会尝试清理资源
        print("正在清理资源...")
