from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import time
import sys
import importlib.util

# 动态导入新的对话管理器
# spec = importlib.util.spec_from_file_location(
#     "dialogue_manager_new",
#     os.path.join(os.path.dirname(__file__), "../core/dialogue_manager_new.py")
# )
# dialogue_manager_module = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(dialogue_manager_module)
# get_dialogue_manager = dialogue_manager_module.get_dialogue_manager
from core.dialogue_manager_new import get_dialogue_manager, DialogueManager

# 创建路由器
router = APIRouter()
dialogue_manager = DialogueManager()
dialogue_manager.charge(model="speak",choice="open")

# 请求模型
class UserInput(BaseModel):
    text: str
    role_id: Optional[str] = None
    stream: Optional[bool] = True


class AudioData(BaseModel):
    audio_data: str  # Base64 编码的音频数据


class RoleRequest(BaseModel):
    role_id: str


# API 路由
@router.post("/chat")
async def chat_with_ai(input_data: UserInput):
    """处理文本聊天请求"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 如果指定了角色，先设置角色
        if input_data.role_id:
            dialogue_manager.set_role(input_data.role_id)
        
        # 设置流式输出标志
        dialogue_manager.stream_voice = input_data.stream
        
        # 处理用户输入
        response = dialogue_manager.process_user_input(input_data.text, speak=False)
        
        # 返回响应和音频URL
        return {
            "response": response, 
            # "audio_urls": dialogue_manager.audio_urls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/recognize")
async def recognize_voice():
    """处理语音识别请求"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 处理音频数据
        result =  dialogue_manager.charge(model="asr",choice="open")

        return {
            "message": result,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/voice/recognize/stop")
async def stop_recognize_voice():
    """停止语音识别请求"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 停止语音识别
        result = dialogue_manager.charge(model="asr", choice="close")
        
        return {
            "message": result,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/speak")
async def synthesize_speech(input_data: UserInput):
    """处理语音合成请求"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 如果指定了角色，先设置角色
        if input_data.role_id:
            dialogue_manager.set_role(input_data.role_id)
        
        # 生成语音
        audio_paths = dialogue_manager.speak(input_data.text)
        
        return {"audio_paths": audio_paths, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/speak/start")
async def synthesize_speech():
    """处理语音合成请求"""
    try:
        result = dialogue_manager.charge(model="tts", choice="open")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/voice/speak/stop")
async def stop_synthesize_speech():
    """处理停止语音合成请求"""
    try:
        result = dialogue_manager.charge(model="tts", choice="close")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/roles")
async def get_roles():
    """获取支持的角色列表"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 获取角色列表
        roles = dialogue_manager.get_supported_roles()
        
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/role/set")
async def set_role(role_request: RoleRequest):
    """设置当前角色"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 设置角色
        success = dialogue_manager.set_role(role_request.role_id)
        print(role_request.role_id)
        print(f"role_id type: {type(role_request.role_id)}, value: {role_request.role_id}")
        
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {"status": "success", "message": f"已设置角色为 {role_request.role_id}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interrupt")
async def interrupt_ai():
    """中断AI语音输出"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 执行中断
        result = dialogue_manager.interrupt_ai()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    try:
        # 简单返回当前时间和系统状态
        return {
            "status": "running",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct-chat")
async def direct_chat_with_model(input_data: UserInput):
    """直接连接到模型的聊天接口"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 如果指定了角色，先设置角色
        if input_data.role_id:
            dialogue_manager.set_role(input_data.role_id)
        
        # 设置流式输出标志
        dialogue_manager.stream_voice = input_data.stream
        
        # 处理用户输入但不自动播放语音
        voice_mode_backup = getattr(dialogue_manager, "voice_mode", True)
        dialogue_manager.voice_mode = False
        
        # 调用聊天代理获取回复
        ai_response = dialogue_manager.process_user_input(input_data.text)
        
        # 恢复设置
        dialogue_manager.voice_mode = voice_mode_backup
        
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct-recognize")
async def direct_recognize(background_tasks: BackgroundTasks, audio_data: AudioData):
    """直接连接到模型的语音识别"""
    try:
        # 获取对话管理器
        # dialogue_manager = get_dialogue_manager()
        
        # 处理音频数据，但不触发自动回复
        result = dialogue_manager.process_audio(audio_data.audio_data)
        
        # 获取最新的识别文本
        recognized_text = dialogue_manager.recognized_text
        
        # 清空当前识别的文本，防止自动处理
        background_tasks.add_task(lambda: setattr(dialogue_manager, "recognized_text", ""))
        
        return {"recognized_text": recognized_text, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
