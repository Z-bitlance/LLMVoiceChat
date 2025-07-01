import os
import time
from idlelib.rpc import response_queue

import requests
import base64
import dashscope
import threading
import queue
import re
import json
import sys
from pathlib import Path

from core.agentChat import AgentChat
# from core.playMp3 import MP3Player

from core.asr import ASRmanager

from core.voiceSpeak import VoiceSpeak

# 添加上级目录到系统路径，以便导入agentChat和playMp3模块
# parent_dir = str(Path(__file__).parent.parent.parent.parent)
# if parent_dir not in sys.path:
#     sys.path.append(parent_dir)

# try:
# sys.path.append(parent_dir)

# except ImportError:
#     print("无法导入必要模块，请确保agentChat.py和playMp3.py在正确的路径上")

# TTS API地址
TTS_API_URL = "http://localhost:51000/api/tts"

# 语音文件存储路径
VOICE_DATA_DIR = Path("backend/static/audio")
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 日志文件路径
LOG_DIR = Path("backend/static/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class DialogueManager:
    def __init__(self):

        # 配置ASR SDK
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "sk-d03c4fe2b7424948a9e3fbc698e35f6f")

        # 对话状态: 'idle', 'user_speaking', 'ai_speaking'
        self.state = "idle"

        # 流式输出标志
        self.stream_voice = True



        self.running = True

        # 音频数据缓冲区和队列
        self.audio_buffer = queue.Queue()
        self.audio_queue = queue.Queue()

        # 识别结果
        # self.recognized_text = ""
        # self.asr_manager.recognized_text = ""

        # 当前角色信息
        self.current_role = {"id": "libai", "name": "李白模拟", "voice": "longshu_v2", "character_id": "e2eed5eed7bb4fa8a75a7b4cfc8fb235"}

        # 初始化聊天代理
        self.agent_chat = AgentChat()
        self.agent_chat.set_get_session_id_callback(self.process_agent_chat_callback)
        # 设置对话sessionID
        self.chat_session_id = None



        # asr代理
        self.asr_manager = None
        # self.asr_manager.start_asr()
        # self.asr_manager.set_text_callback(self.process_asr_callback)

        # 语音合成服务
        self.voice_speak = None
        # self.voice_speak.set_callback(self.process_speak_callback)

    def charge(self ,model=None, choice=None):
        if model == "asr" and choice == "open":
            self.asr_manager = ASRmanager()
            self.asr_manager.start_asr()
            self.asr_manager.set_text_callback(self.process_asr_callback)
            return "ASR服务已启动"
        elif model == "asr" and choice == "close":
            self.asr_manager.stop_asr()
            self.asr_manager = None
        if model == "tts" and choice == "open":
            self.voice_speak = VoiceSpeak()
            self.voice_speak.set_callback(self.process_speak_callback)
            return "TTS服务已启动"
        elif model == "tts" and choice == "close":
            self.voice_speak = None

    # Callback处理函数设置
    # ---------------------------------------------------------------
    def process_asr_callback(self, text):
        if self.state == "idle":
            self.state = "user_speaking"
            response=self.process_user_input(text)

            self.state = "ai_speaking"
            self.speak(response)

        elif self.state == "ai_speaking":
            try:
                self.voice_speak.interrupt_ai()
            except Exception as e:
                print(f"中断AI语音失败: {e}")
            self.state="user_speaking"
            response=self.process_user_input(text)

            self.state = "ai_speaking"
            self.speak(response)

        elif self.state == "user_speaking":
            try:
                self.voice_speak.interrupt_ai()
            except Exception as e:
                print(f"中断AI语音失败: {e}")
            response=self.process_user_input(text)

            self.state = "user_speaking"
            self.speak(response)


    def process_speak_callback(self):
        self.state = "idle"

    def process_agent_chat_callback(self, session_id):
        self.chat_session_id = session_id
        print(f"当前对话sessionID: {self.chat_session_id}")

    # ----------------------------------------------------------------------------

    def process_user_input(self, text, speak=True):
        """处理用户输入并获取AI响应"""
        print(f'用户问题: {text}, 时间: {time.strftime("%Y%m%d_%H%M%S")}')

        # 调用聊天代理获取回复
        ai_response = self.agent_chat.send_message(text=text)
        print(f'AI回答: {ai_response}, 时间: {time.strftime("%Y%m%d_%H%M%S")}')

        # 记录对话历史
        self._log_conversation(text, ai_response)

        return ai_response


    def _log_conversation(self, user_input, ai_response):
        """记录对话历史"""
        try:
            log_file = LOG_DIR / f'sessionID_{self.chat_session_id}.json'

            with open(log_file, "a", encoding="utf-8") as f:
                json.dump({
                    "user_input": user_input,
                    "ai_response": ai_response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "role": self.current_role["id"] 
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录对话历史失败: {e}")


    def speak(self, text, speak_model="normal"):
        if not self.voice_speak:
            print("语音合成服务未启动，请先调用charge(model='speak', choice='open')")
            return
        if speak_model == "normal":
            self.voice_speak.speak(text=text)
        elif speak_model == "stream":
            self.voice_speak.stream_speak(text=text)
        elif speak_model == "whole":
            self.voice_speak.whole_speak(text=text)

    # 角色人设，音色，历史对话记录设置
    #----------------------------------------------------------------

    def get_supported_roles(self):
        """获取支持的角色列表"""
        return [
            {"id": "libai", "name": "李白模拟", "voice": "longshu_v2", "character_id": "e2eed5eed7bb4fa8a75a7b4cfc8fb235"},
            {"id": "nekogirl", "name": "猫娘", "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6", "character_id": "5ffe587bb14941cda6012bffe3ac3f46"},#猫娘dong,目前猫娘声音与雪莲agent还没调教好，先用相同的voice
            {"id": "dongxuelian", "name": "东雪莲", "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6","character_id": "583dcf485ec14ae39733a0880daa2215"},
            {"id": "yunli", "name": "云璃", "voice": "cosyvoice-v2-prefix-0b859e34494541c3ae4d2fa1e5e6d3a9","character_id": "5ffe587bb14941cda6012bffe3ac3f46"},
            {"id": "storyteller", "name": "讲故事的人", "voice": "sijia"},
            {"id": "direct_model", "name": "直接模型", "voice": "longxiang"},
        ]

    def set_role(self, role_id):
        """设置当前使用的角色"""
        for role in self.get_supported_roles():
            if role["id"] == role_id:
                print(role)
                self.current_role = role
                self.agent_chat.select_character(role["character_id"])
                try:
                 self.voice_speak.set_current_role(role)
                except Exception as e:
                    print(f"设置角色语音失败: {e}")
                return True
        return False
    
    def set_chat_session_id(self, session_id):
        """设置对话sessionID"""
        self.chat_session_id = session_id
        self.agent_chat.set_session_id(session_id)
        print(f"对话sessionID已设置为: {self.chat_session_id}")
    #-----------------------------------------------------------------------------------

    def stop(self):
        """停止对话管理器"""
        self.state = "idle"
        # self.player.stop()
        self.asr_manager.stop_asr()  # 停止ASR服务
        self.asr_manager = None
        self.voice_speak = None


    # def interrupt_ai(self):
    #     """中断AI语音输出"""
    #     try:
    #         print("处理中断AI请求")
    #         self.state = "idle"
    #         self.player.stop()  # 停止当前播放的音频'
    #         time.sleep(0.1)
    #         if not self.player.is_complete():
    #             self.player.__init__()
    #         return {"status": "success", "message": "AI响应已中断"}
    #     except Exception as e:
    #         print(f"中断AI时出错: {e}")
    #         return {"status": "error", "message": str(e)}




# 单例模式
dialogue_manager = DialogueManager()



def get_dialogue_manager():
    """获取对话管理器单例"""
    global dialogue_manager
    if dialogue_manager is None:
        dialogue_manager = DialogueManager()
    return dialogue_manager

if __name__ == "__main__":
    manager = DialogueManager()

    # manager.charge(model="speak", choice="open")
    manager.charge(model="asr", choice="open")
    manager.set_role("libai")

    # manager.set_role("nekogirl")


    try:
        # command = input("输入'sm'启动流式对话系统")
        # if command.lower() == 'sm':
        #     manager.stream_voice = True
        # # 启动对话系统
        #
        # manager.start()

        # 保持程序运行
        while True:
            command = input("输入'q'退出系统,输入sp立即停止语音: ")
            if command.lower() == 'q':
                break
            elif command.lower() == 'dongxuelian':
                 manager.set_role("dongxuelian")
            # elif command.lower() == 'enter':
            #     manager.process_user_input(manager.recognized_text)
            # elif command.lower() == 'text':
            #     print(manager.recognized_text)
            else:

                # 直接对话
                manager.process_asr_callback(command)
    except KeyboardInterrupt:
        print("检测到Ctrl+C，正在退出...")
    finally:
        # 关闭系统
        manager.stop()
