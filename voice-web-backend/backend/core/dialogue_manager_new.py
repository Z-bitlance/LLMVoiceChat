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

from agentChat import AgentChat

from playMp3 import MP3Player

from asr import ASRmanager

from voiceSpeak import VoiceSpeak

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

        # 初始化聊天代理

        self.agent_chat = AgentChat()

        self.asr_manager = ASRmanager()
        self.asr_manager.start_asr()
        self.asr_manager.set_text_callback(self.process_asr_callback)

        self.voice_speak = VoiceSpeak()
        self.voice_speak.set_callback(self.process_speak_callback)
        # # 线程锁
        # self.buffer_thread_lock = threading.Lock()
        # self.buffer_thread = None
        # self.buffer_thread_running = False
        #
        # # 当前选择的角色
        # self.current_role = {
        #     "id": "assistant",
        #     "name": "AI助手",
        #     "voice": "longxiang"
        # }
        #
        # # 音频播放器
        #
        # self.player = MP3Player()

        # # 用于控制语音输出的模式
        # self.voice_mode = True

        # 用于存储生成的音频URL

    # def _mock_player(self):
    #     """模拟MP3Player功能"""
    #
    #     class MockPlayer:
    #         def play(self, file_path):
    #             print(f"[模拟播放] {file_path}")
    #             return True
    #
    #         def stop(self):
    #             print("[模拟播放] 停止播放")
    #             return True
    #
    #         def is_complete(self):
    #             return True
    #
    #     self.player = MockPlayer()

    # def _mock_agent_chat(self):
    #     """当正式AgentChat不可用时的模拟实现"""
    #
    #     class MockAgentChat:
    #         def __init__(self):
    #             self.last_response = None
    #
    #         def send_message(self, text):
    #             response = f'这是对"{text}"的模拟回复。真实系统会连接到您的AI大模型。'
    #             self.last_response = response
    #             return response
    #
    #         def reset_session(self):
    #             pass
    #
    #     return MockAgentChat()

    # def init_asr(self):
    #     """初始化语音识别"""
    #     try:
    #         # 配置ASR回调
    #         class ASRCallback(dashscope.audio.asr.TranslationRecognizerCallback):
    #             def __init__(self, manager):
    #                 self.manager = manager
    #
    #             def on_open(self):
    #                 print("语音识别已启动")
    #
    #             def on_close(self):
    #                 print("语音识别已关闭")
    #
    #             def on_event(self, request_id, transcription_result, translation_result, usage):
    #                 if transcription_result is not None:
    #                     self.manager.recognized_text = transcription_result.text
    #                     print(f"识别到: {self.manager.recognized_text}")
    #
    #                     # 如果AI正在说话，打断它
    #                     if self.manager.state == "ai_speaking":
    #                         self.manager.interrupt_ai()
    #
    #         self.asr_callback = ASRCallback(self)
    #         self.translator = dashscope.audio.asr.TranslationRecognizerRealtime(
    #             model="gummy-realtime-v1",
    #             format="pcm",
    #             sample_rate=16000,
    #             transcription_enabled=True,
    #             translation_enabled=False,
    #             callback=self.asr_callback,
    #         )
    #
    #         # 初始化运行标志和线程
    #         self.running = True
    #         return True
    #     except Exception as e:
    #         print(f"初始化语音识别失败: {e}")
    #         return False
    #
    # def start_asr(self):
    #     """启动语音识别服务"""
    #     try:
    #         if not hasattr(self, 'translator'):
    #             if not self.init_asr():
    #                 return False
    #
    #         self.translator.start()
    #
    #         # 启动处理线程
    #         self.asr_thread = threading.Thread(target=self.asr_process_loop)
    #         self.detection_thread = threading.Thread(target=self.detect_user_speech)
    #
    #         self.asr_thread.daemon = True
    #         self.detection_thread.daemon = True
    #
    #         self.asr_thread.start()
    #         self.detection_thread.start()
    #
    #         print("语音识别服务已启动")
    #         return True
    #     except Exception as e:
    #         print(f"启动语音识别服务失败: {e}")
    #         return False
    #
    # def stop_asr(self):
    #     """停止语音识别服务"""
    #     try:
    #         self.running = False
    #         if hasattr(self, 'translator'):
    #             self.translator.stop()
    #         print("语音识别服务已停止")
    #         return True
    #     except Exception as e:
    #         print(f"停止语音识别服务失败: {e}")
    #         return False
    #
    # def asr_process_loop(self):
    #     """持续处理音频数据"""
    #     print("音频处理线程已启动")
    #     while self.running:
    #         try:
    #             if self.audio_buffer.empty():
    #                 time.sleep(0.1)
    #                 continue
    #
    #             data = self.audio_buffer.get()
    #             self.translator.send_audio_frame(data)
    #         except Exception as e:
    #             print(f"处理音频数据错误: {e}")
    #             time.sleep(0.1)

    # def detect_user_speech(self):
    #     """检测用户是否开始说话"""
    #     print("检测用户语音线程已启动")
    #     silence_threshold = 5  # 静音阈值，需根据实际环境调整
    #     silence_frames = 0
    #     talking_frames = 0
    #     silence_duration = 1.0  # 多少秒的沉默后处理识别文本
    #     silence_frames_limit = int(silence_duration / 0.05)  # 以50ms为单位的帧数
    #
    #     while self.running:
    #         try:
    #             if self.asr_manager.audio_buffer.empty():
    #                 time.sleep(0.1)
    #                 continue
    #
    #             audio_data = self.asr_manager.audio_buffer.get()
    #             volume = sum(abs(int.from_bytes(audio_data[i:i + 2], 'little', signed=True))
    #                          for i in range(0, len(audio_data), 2)) / (len(audio_data) / 2)
    #
    #             # 根据音量判断用户是否在说话
    #             if volume > silence_threshold:
    #                 talking_frames += 1
    #                 silence_frames = 0
    #                 if talking_frames > 3:  # 连续3帧以上有声音才认为是说话开始
    #                     print(f"检测到用户说话，音量: {volume}, 当前状态: {self.state}")
    #
    #                     if self.state == "ai_speaking":
    #                         print("检测到用户说话，打断AI...")
    #                         self.interrupt_ai()
    #                     self.state = "user_speaking"
    #             else:
    #                 silence_frames += 1
    #                 talking_frames = 0
    #
    #                 # 如果用户停止讲话超过设定的时间，并且之前状态是用户讲话
    #                 if silence_frames > silence_frames_limit and self.state == "user_speaking":
    #                     print(f"检测到用户停止说话，沉默帧数: {silence_frames}")
    #                     print(f"当前识别文本: '{self.recognized_text}'")
    #                     self.state = "idle"
    #
    #                     # 如果有识别到的文本，则处理
    #                     if self.recognized_text and len(self.recognized_text.strip()) > 0:
    #                         print("处理识别到的文本...")
    #                         self.process_user_input(self.recognized_text)
    #                         self.recognized_text = ""
    #
    #             time.sleep(0.05)
    #         except Exception as e:
    #             print(f"检测用户语音错误: {e}")
    #             time.sleep(0.1)

    # def process_one_time_audio(self, audio_data):
    #     """处理一次性发送的音频数据进行识别
    #
    #     Args:
    #         audio_data: Base64编码的音频数据
    #
    #     Returns:
    #         dict: 包含识别状态和识别文本的字典
    #     """
    #     try:
    #         print("处理一次性音频数据...:", audio_data[:50])
    #         # 将Base64编码的音频转换为二进制
    #         binary_audio = base64.b64decode(audio_data)
    #
    #         # 创建存储结果的容器和事件
    #         result = {"text": ""}
    #         recognition_done = threading.Event()
    #
    #         def process_audio_thread():
    #             try:
    #                 # 创建临时回调
    #                 class TempCallback(dashscope.audio.asr.TranslationRecognizerCallback):
    #                     def __init__(self):
    #                         self.collected_text = ""
    #
    #                     def on_event(self, request_id, transcription_result, translation_result, usage):
    #                         if transcription_result is not None:
    #                             self.collected_text = transcription_result.text
    #                             print(f"临时识别器识别到: {self.collected_text}")
    #
    #                     def on_error(self, err):
    #                         print(f"临时识别器错误: {err}")
    #                         recognition_done.set()
    #
    #                     def on_close(self):
    #                         recognition_done.set()
    #
    #                 callback = TempCallback()
    #
    #                 # 创建临时翻译器
    #                 translator = dashscope.audio.asr.TranslationRecognizerRealtime(
    #                     model="gummy-realtime-v1",
    #                     format="pcm",
    #                     sample_rate=16000,
    #                     transcription_enabled=True,
    #                     translation_enabled=False,
    #                     callback=callback,
    #                 )
    #
    #                 # 开始识别
    #                 translator.start()
    #                 translator.send_audio_frame(binary_audio)
    #
    #                 # 等待一段时间以确保识别完成
    #                 time.sleep(2.0)
    #
    #                 # 保存结果并清理
    #                 result["text"] = callback.collected_text
    #                 translator.stop()
    #
    #             except Exception as e:
    #                 print(f"临时音频识别线程错误: {e}")
    #             finally:
    #                 # 标记识别完成
    #                 recognition_done.set()
    #
    #         # 启动临时识别线程
    #         thread = threading.Thread(target=process_audio_thread)
    #         thread.daemon = True
    #         thread.start()
    #
    #         # 等待识别完成或超时
    #         if not recognition_done.wait(timeout=5.0):
    #             print("一次性音频识别超时")
    #
    #         return {
    #             "status": "success",
    #             "message": "一次性音频数据已处理",
    #             "recognized_text": result["text"]
    #         }
    #     except Exception as e:
    #         print(f"处理一次性音频数据错误: {e}")
    #         return {"status": "error", "message": str(e)}
    #
    # def process_audio(self, audio_data):
    #     """处理从前端发送的音频数据"""
    #     try:
    #         # 将Base64编码的音频转换为二进制
    #         binary_audio = base64.b64decode(audio_data)
    #
    #         # 加入音频缓冲区
    #         self.asr_manager.audio_buffer.put(binary_audio)
    #
    #         # 如果ASR服务未启动，则尝试启动
    #         # if not hasattr(self, 'translator') or not hasattr(self, 'asr_thread') or not self.asr_thread.is_alive():
    #         #     self.start_asr()
    #         # else:
    #         # 计算音频音量以进行语音活动检测
    #         volume = sum(abs(int.from_bytes(binary_audio[i:i + 2], 'little', signed=True))
    #                      for i in range(0, len(binary_audio), 2)) / (len(binary_audio) / 2)
    #
    #         # 音量阈值（可根据实际环境调整）
    #         silence_threshold = 0
    #
    #         if volume > silence_threshold and self.state == "ai_speaking":
    #             print(f"实时检测到用户打断，音量: {volume}")
    #             self.interrupt_ai()
    #         print("识别文本：", self.recognized_text)
    #
    #         return {
    #             "status": "success",
    #             "message": "音频数据已接收",
    #             "recognized_text": self.recognized_text
    #         }
    #     except Exception as e:
    #         print(f"处理音频数据错误: {e}")
    #         return {"status": "error", "message": str(e)}

    def process_asr_callback(self, text):
        if self.state == "idle":
            self.state = "user_speaking"
            response=self.process_user_input(text)

            self.state = "ai_speaking"
            self.speak(response)

        elif self.state == "ai_speaking":
            self.voice_speak.interrupt_ai()
            self.state="user_speaking"
            response=self.process_user_input(text)

            self.state = "ai_speaking"
            self.speak(response)

        elif self.state == "user_speaking":
            self.voice_speak.interrupt_ai()
            response=self.process_user_input(text)

            self.state = "user_speaking"
            self.speak(response)


    def process_speak_callback(self):
        self.state = "idle"


    def process_user_input(self, text, speak=True):
        """处理用户输入并获取AI响应"""
        print(f'用户问题: {text}, 时间: {time.strftime("%Y%m%d_%H%M%S")}')

        # 调用聊天代理获取回复
        ai_response = self.agent_chat.send_message(text=text)

        # 记录对话历史
        self._log_conversation(text, ai_response)

        return ai_response

    def charge_asr(self, charge=None):
        if charge == "open":
            self.asr_manager.start_asr()
        elif charge == "close":
            self.asr_manager.stop_asr()

    def _log_conversation(self, user_input, ai_response):
        """记录对话历史"""
        try:
            log_file = LOG_DIR / f'conversation_{time.strftime("%Y%m%d_%H%M%S")}.json'

            with open(log_file, "w", encoding="utf-8") as f:
                json.dump({
                    "user_input": user_input,
                    "ai_response": ai_response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "role": self.voice_speak.current_role["id"]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录对话历史失败: {e}")

    # def response_split(self, text):
    #     """将AI响应文本分割成多段"""
    #     segments = re.split(r'(?<=[。！？.!?])', text)
    #     print("分割文本片段：", [str(i) for i in segments if i != ''])
    #     return [segment.strip() for segment in segments if segment != '']
    #
    # def speak(self, text):
    #     """
    #         分段处理并播放AI回应
    #         创建音频缓冲池，将长文本分割为多个短句，依次合成音频并播放
    #         """
    #     self.state = "ai_speaking"
    #     print(f"AI回答（stream）: {text}")
    #     audio_urls = []
    #     # 创建音频文件队列
    #
    #     # 使用锁确保线程安全
    #     with self.buffer_thread_lock:
    #         self.buffer_thread_running = True
    #
    #     def audio_queue_add(segments, audio_queue, audio_urls):
    #         for segment in segments:
    #             if not self.buffer_thread_running:
    #                 print("音频播放被中断")
    #                 break
    #
    #             try:
    #                 # 请求TTS API生成语音
    #                 response = requests.post(TTS_API_URL, json={
    #                     "text": segment,
    #                     "voice": self.current_role["voice"],
    #                     "model": "cosyvoice-v2"
    #                 })
    #
    #                 if response.status_code == 200:
    #                     try:
    #                         # 解析API响应获取文件路径
    #                         response_data = response.json()
    #                         if "file_path" in response_data:
    #                             output_file = response_data["file_path"]
    #                         else:
    #                             # 如果响应不包含路径，保存为临时文件
    #                             output_file = f"./VoiceData/temp_{int(time.time())}.mp3"
    #                             with open(output_file, 'wb') as f:
    #                                 f.write(response.content)
    #
    #                         # 将音频文件加入队列
    #                         audio_queue.put(output_file)
    #                         audio_urls.append(output_file)
    #                         print(f"已添加音频片段: {output_file},时间: {time.strftime('%Y%m%d_%H%M%S')}")
    #                     except ValueError as e:
    #                         print("处理TTS响应时出错:", str(e))
    #                 else:
    #                     print(f"TTS API请求失败: {response.status_code}, {response.text}")
    #             except Exception as e:
    #                 print(f"处理音频段落时出错: {str(e)}")
    #
    #     def audio_queue_play(audio_queue):
    #         while self.buffer_thread_running:
    #             if audio_queue.empty():
    #                 time.sleep(0.2)
    #             else:
    #                 try:
    #                     # 等待播放完成
    #                     while not self.player.is_complete() and self.buffer_thread_running:
    #                         time.sleep(0.4)
    #
    #                     file_path = audio_queue.get()
    #
    #                     print(f"正在播放片段: {file_path}")
    #
    #                     if os.path.exists(file_path):
    #                         self.player.play(file_path)
    #                     else:
    #                         print(f"文件不存在: {file_path}")
    #                 except Exception as e:
    #                     print(f"播放音频片段时出错: {str(e)}")
    #                     time.sleep(0.5)
    #                     # 继续处理下一个音频，而不是中断整个循环
    #                     continue
    #
    #     # 在后台线程中处理TTS请求和播放
    #     def process_and_play():
    #         try:
    #             audio_queue = queue.Queue()
    #
    #             # 分割文本
    #             segments = self.response_split(text)
    #
    #             # 创建两个独立线程
    #             add_thread = threading.Thread(target=audio_queue_add, args=(segments, audio_queue, audio_urls))
    #             play_thread = threading.Thread(target=audio_queue_play, args=(audio_queue,))
    #
    #             add_thread.daemon = True
    #             play_thread.daemon = True
    #
    #             # 启动线程
    #             play_thread.start()  # 先启动播放线程
    #             add_thread.start()  # 再启动添加线程
    #
    #             # 等待添加线程完成
    #             add_thread.join()
    #
    #             # 等待队列中的所有音频播放完毕
    #             while not audio_queue.empty() and self.buffer_thread_running:
    #                 time.sleep(0.2)
    #
    #             # 结束播放线程
    #             self.buffer_thread_running = False
    #         finally:
    #             with self.buffer_thread_lock:
    #                 if self.buffer_thread_running:  # 只有在没被中断的情况下才重置状态
    #                     self.state = "idle"
    #                     self.buffer_thread_running = False
    #
    #     # 创建并启动音频处理线程
    #     with self.buffer_thread_lock:
    #         self.buffer_thread = threading.Thread(target=process_and_play)
    #         self.buffer_thread.daemon = True
    #         self.buffer_thread.start()
    def speak(self, text, speak_model="normal"):
        if speak_model == "normal":
            self.voice_speak.speak(text=text)
        elif speak_model == "stream":
            self.voice_speak.stream_speak(text=text)

    def get_supported_roles(self):
        """获取支持的角色列表"""
        return [
            {"id": "libai", "name": "李白模拟", "voice": "longshu-v2","character_id": "5ffe587bb14941cda6012bffe3ac3f46"},
            {"id": "nekogirl", "name": "猫娘", "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6", "character_id": "e2eed5eed7bb4fa8a75a7b4cfc8fb235"},#猫娘dong,目前猫娘声音与雪莲agent还没调教好，先用相同的voice
            {"id": "dongxuelian", "name": "东雪莲", "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6"},
            {"id": "yunli", "name": "云璃", "voice": "cosyvoice-v2-prefix-0b859e34494541c3ae4d2fa1e5e6d3a9"},
            {"id": "storyteller", "name": "讲故事的人", "voice": "sijia"},
            {"id": "direct_model", "name": "直接模型", "voice": "longxiang"},
        ]

    def set_role(self, role_id):
        """设置当前使用的角色"""
        for role in self.get_supported_roles():
            if role["id"] == role_id:
                self.voice_speak.set_current_role(role["character_id"])
                self.agent_chat.select_character(role_id[id])
                return True
        return False

    def stop(self):
        """<UNK>"""
        self.state = "idle"
        # self.player.stop()
        self.asr_manager = None


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
                 manager.set_role("nekogirl")
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
