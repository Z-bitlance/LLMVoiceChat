import requests
import time
import threading
from pathlib import Path
import os
import queue
import re

from core.playMp3 import MP3Player
from dotenv import load_dotenv
# 加载环境变量
load_dotenv('voice-web-backend/backend/.env.local')
apiKey = os.getenv('dashscope_api_key')
tts_port = os.getenv('tts_port', '51000')
TTS_API_URL = f"http://localhost:{tts_port}/api/api/tts"

# 语音文件存储路径
VOICE_DATA_DIR = Path("backend/static/audio")
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)


class VoiceSpeak:
    def __init__(self):
        self.player = MP3Player()
        self.buffer_thread_lock = threading.Lock()
        self.buffer_thread = None
        self.buffer_thread_running = False

        self.player_lock = False

        self.tts_request_count=0

        # 当前选择的角色
        self.current_role = {
            "id": "assistant",
            "name": "AI助手",
            "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6",
        }

        print("VoiceSpeak model initialized")



    def set_current_role(self, role):
        self.current_role["id"] = role["id"]
        self.current_role["name"] = role["name"]
        self.current_role["voice"] = role["voice"]

    def response_split(self, text):
        """将AI响应文本分割成多段"""
        segments = re.split(r'(?<=[。！？.!?])', text)
        print("分割文本片段：", [str(i) for i in segments if i != ''])
        return [segment.strip() for segment in segments if segment != '']
    def interrupt_ai(self):
        """中断AI语音输出"""
        try:
            print("处理中断AI请求")
            
            # 确保播放器正确初始化
            if not self.ensure_player_initialized():
                return {"status": "error", "message": "播放器初始化失败"}
            
            # 停止当前播放的音频
            self.player.stop()
              # 安全地检查播放是否完成
            try:
                if hasattr(self.player, 'is_complete') and not self.player.is_complete():
                    self.player.__init__()
            except Exception as e:
                print(f"检查播放完成状态时出错: {e}")
                # 重新初始化播放器
                try:
                    self.player.__init__()
                except Exception as init_error:
                    print(f"重新初始化播放器时出错: {init_error}")
                    
            # 设置锁定状态和停止缓冲线程
            self.player_lock = True
            self.buffer_thread_running = False
            
            return {"status": "success", "message": "AI响应已中断"}
        except Exception as e:
            print(f"中断AI时出错: {e}")
            return {"status": "error", "message": str(e)}


    def stream_speak(self, text):
        print("on test")

    def whole_speak(self, text ,file_url=None):
        audio_queue = queue.Queue()
        try:
            # 请求TTS API生成语音
            response = requests.post(TTS_API_URL, json={
                "text": text,
                "voice": self.current_role["voice"],
                "model": "cosyvoice-v2"
            })

            if response.status_code == 200:
                try:
                    # 解析API响应获取文件路径
                    response_data = response.json()
                    if "file_path" in response_data:
                        output_file = response_data["file_path"]
                    else:
                        # 如果响应不包含路径，保存为临时文件
                        output_file = f"voice-web-backend/backend/static/audio/temp_{int(time.time())}.mp3"
                        with open(output_file, 'wb') as f:
                            f.write(response.content)

                    audio_queue.put(output_file)
                except Exception as e:
                    print(f"解析音频时发生错误: {e}")
        except Exception as e:
            print(f"获取音频时发生错误: {e}")

        if not audio_queue.empty():
            output_file = audio_queue.get()

            if os.path.exists(output_file):
                self.player.play(output_file)
            else:
                print(f"文件不存在: {output_file}")

    def speak(self, text):
        """
            分段处理并播放AI回应
            创建音频缓冲池，将长文本分割为多个短句，依次合成音频并播放
            """
        
        audio_urls = []
        # 创建音频文件队列

        # 使用锁确保线程安全
        with self.buffer_thread_lock:
            self.buffer_thread_running = True

        def audio_queue_add(segments, audio_queue, audio_urls):
            for segment in segments:
                if not self.buffer_thread_running:
                    print("音频播放被中断")
                    break

                try:
                    # 请求TTS API生成语音
                    response = requests.post(TTS_API_URL, json={
                        "text": segment,
                        "voice": self.current_role["voice"],
                        "model": "cosyvoice-v2"
                    })

                    if response.status_code == 200:
                        try:
                            # 解析API响应获取文件路径
                            response_data = response.json()
                            if "file_path" in response_data:
                                output_file = response_data["file_path"]
                            else:
                                # 如果响应不包含路径，保存为临时文件
                                output_file = f"voice-web-backend/backend/static/audio/temp_{int(time.time())}.mp3"
                                with open(output_file, 'wb') as f:
                                    f.write(response.content)

                            # 将音频文件加入队列
                            audio_queue.put(output_file)
                            audio_urls.append(output_file)
                            print(f"已添加音频片段: {output_file},时间: {time.strftime('%Y%m%d_%H%M%S')}")
                        except ValueError as e:
                            print("处理TTS响应时出错:", str(e))
                    else:
                        print(f"TTS API请求失败: {response.status_code}, {response.text}")
                except Exception as e:
                    print(f"处理音频段落时出错: {str(e)}")        
        def audio_queue_play(audio_queue):
            while self.buffer_thread_running:
                if audio_queue.empty():
                    time.sleep(0.2)
                else:
                    try:
                        # 等待播放完成 - 安全检查
                        while self.buffer_thread_running:
                            try:
                                if hasattr(self.player, 'is_complete') and not self.player.is_complete():
                                    time.sleep(0.4)
                                else:
                                    break
                            except Exception as e:
                                print(f"检查播放状态时出错: {e}")
                                break
                            time.sleep(0.4)

                        file_path = audio_queue.get()

                        print(f"正在播放片段: {file_path}")

                        if os.path.exists(file_path):
                            self.player.play(file_path)
                        else:
                            print(f"文件不存在: {file_path}")
                    except Exception as e:
                        print(f"播放音频片段时出错: {str(e)}")
                        time.sleep(0.5)
                        # 继续处理下一个音频，而不是中断整个循环
                        continue


        # 在后台线程中处理TTS请求和播放
        def process_and_play():
            try:
                audio_queue = queue.Queue()

                # 分割文本
                segments = self.response_split(text)

                # 创建两个独立线程
                add_thread = threading.Thread(target=audio_queue_add, args=(segments, audio_queue, audio_urls))
                play_thread = threading.Thread(target=audio_queue_play, args=(audio_queue,))

                add_thread.daemon = True
                play_thread.daemon = True

                # 启动线程
                play_thread.start()  # 先启动播放线程
                add_thread.start()  # 再启动添加线程

                # 等待添加线程完成
                add_thread.join()
                play_thread.join()

                # 等待队列中的所有音频播放完毕
                while not audio_queue.empty() and self.buffer_thread_running:
                    time.sleep(0.2)                # 结束播放线程
                self.buffer_thread_running = False
            finally:
                with self.buffer_thread_lock:
                    if self.buffer_thread_running:  # 只有在没被中断的情况下才重置状态
                        # self.state = "idle"
                        self.buffer_thread_running = False
                # 安全调用回调函数
                if self.playing_complete_callback and callable(self.playing_complete_callback):
                    try:
                        self.playing_complete_callback()
                    except Exception as e:
                        print(f"调用播放完成回调函数时出错: {e}")
                else:
                    print("播放完成回调函数未设置或不可调用")

        # 创建并启动音频处理线程
        with self.buffer_thread_lock:
            self.buffer_thread = threading.Thread(target=process_and_play)
            self.buffer_thread.daemon = True
            self.buffer_thread.start()

    def set_callback(self, callback):
        self.playing_complete_callback = callback
        print("callback function has been set")

    def ensure_player_initialized(self):
        """确保播放器被正确初始化"""
        if not hasattr(self, 'player') or self.player is None:
            try:
                self.player = MP3Player()
                print("播放器已重新初始化")
            except Exception as e:
                print(f"重新初始化播放器失败: {e}")
                return False
        return True

def test():
    a = VoiceSpeak()
    a.set_current_role({"id": "dongxuelian", "name": "东雪莲", "voice": "cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6","character_id": "583dcf485ec14ae39733a0880daa2215"})





