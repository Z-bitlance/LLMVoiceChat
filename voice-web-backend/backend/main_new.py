import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys

# 添加项目根目录到系统路径
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

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


# 直接运行应用
if __name__ == "__main__":
    try:
        print("启动语音对话系统后端...")
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run("main_new:app", host="0.0.0.0", port=port, reload=True)
    except Exception as e:
        print(f"启动服务失败: {e}")
