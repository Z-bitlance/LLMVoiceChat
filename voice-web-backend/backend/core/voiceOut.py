import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
import uvicorn

from playsound import playsound
import threading
import time

# 设置API密钥
dashscope.api_key = "sk-d03c4fe2b7424948a9e3fbc698e35f6f"

# 创建输出目录
OUTPUT_DIR = "VoiceData"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 创建FastAPI应用
app = FastAPI(title="文本转语音服务")


# 定义请求数据模型
class TTSRequest(BaseModel):
    text: str
    model: str = "cosyvoice-v2"
    voice: str = "longshu-v2"


@app.post("/api/tts")
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
        output_file = f'D:/pythonprojects/pythonProject/model/VoicePut/VoiceData/temp_{time.strftime("%Y%m%d_%H%M%S")}.mp3'

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
        print()
        raise HTTPException(status_code=500, detail=f"语音生成失败: {str(e)}")


@app.post("/api/tts/play")
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
    uvicorn.run(app, host="0.0.0.0", port=51000)