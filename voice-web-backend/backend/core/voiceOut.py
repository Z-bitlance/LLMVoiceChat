import os
import uuid
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
import uvicorn

from playsound import playsound
import threading
import time
from dotenv import load_dotenv
# 加载环境变量
load_dotenv('../.env')
apiKey = os.getenv('dashscope_api_key')
tts_port = os.getenv('tts_port', '51000')

# 设置API密钥
dashscope.api_key = apiKey

# 创建输出目录
OUTPUT_DIR = "voice-web-backend/backend/static/audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 创建FastAPI应用
app = FastAPI(title="文本转语音服务")
router = APIRouter()


# 定义请求数据模型
class TTSRequest(BaseModel):
    text: str
    model: str = "cosyvoice-v2"
    voice: str = "longshu_v2"


@router.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """
    将文本转换为语音并返回MP3文件
    """
    try:
        # 初始化语音合成器
        synthesizer = SpeechSynthesizer(model=request.model, voice=request.voice)
        # 生成语音
        audio = synthesizer.call(request.text)
        # 生成唯一文件名
        output_file = f'voice-web-backend/backend/static/audio/temp_{time.strftime("%Y%m%d_%H%M%S")}.mp3'

        # 保存音频文件
        with open(output_file, 'wb') as f:

            f.write(audio)

        return {"status": "success", "message": "语音生成成功", "file_path": output_file}
        # 返回文件
        # return FileResponse(
        #     path=output_file,
        #     media_type="audio/mp3",
        #     filename=output_file
        # )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音生成失败: {str(e)}")


@router.post("/api/tts/play")
async def text_to_speech_play(request: TTSRequest):
    """
    将文本转换为语音并通过系统扬声器播放
    """
    try:
        # 初始化语音合成器
        synthesizer = SpeechSynthesizer(model=request.model, voice=request.voice)

        # 生成语音
        audio = synthesizer.call(request.text)

        # 生成唯一文件名
        output_file = f"{OUTPUT_DIR}/{uuid.uuid4()}.mp3"

        # 保存音频文件
        with open(output_file, 'wb') as f:
            f.write(audio)

        # 在后台线程中播放音频，避免阻塞API响应
        def play_audio():
            playsound(output_file)

        threading.Thread(target=play_audio).start()

        # 返回成功信息
        return {"status": "success", "message": "正在播放音频", "file_path": output_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音生成或播放失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=tts_port)