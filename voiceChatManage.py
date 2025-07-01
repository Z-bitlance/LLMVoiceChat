import threading
import time
import queue
import pyaudio
import requests
import os
import dashscope
from dashscope.audio.asr import *
from voiceScripts.agentChat import AgentChat
from playMp3 import MP3Player
import re

# TTS API地址
TTS_API_URL = "http://localhost:51000/api/tts"


class DialogueManager:
    def __init__(self):
        # 对话状态: 'idle', 'user_speaking', 'ai_speaking'
        self.state = "idle"

        #流式输出标志
        self.stream_voice = False

        # 音频数据缓冲区
        self.audio_buffer = queue.Queue()

        # 音频数据队列，用于实时处理音频流
        self.audio_queue = queue.Queue()

        # 识别结果
        self.recognized_text = ""

        # 当前正在播放的语音进程
        self.current_speech_process = None

        # 初始化语音识别
        self.init_asr()

        # 初始化音频设备
        self.init_audio()

        self.player = MP3Player()
        self.agentchat = AgentChat()

        # 控制线程
        self.running = True
        self.asr_thread = threading.Thread(target=self.asr_process_loop)
        self.detection_thread = threading.Thread(target=self.detect_user_speech)

        # 语音流式输出线程
        self.buffer_thread_lock = threading.Lock()
        self.buffer_thread = None
        self.buffer_thread_running = False

    def init_asr(self):
        # 配置ASR回调
        class ASRCallback(TranslationRecognizerCallback):
            def __init__(self, manager):
                self.manager = manager

            def on_open(self):
                print("语音识别已启动")

            def on_close(self):
                print("语音识别已关闭")

            def on_event(self, request_id, transcription_result, translation_result, usage):
                if transcription_result is not None:
                    self.manager.recognized_text = transcription_result.text
                    self.recognized_text = self.manager.recognized_text
                    print(f"识别到: {self.manager.recognized_text}")

                    # 如果AI正在说话，打断它
                    # if self.manager.state == "ai_speaking":
                    #     self.manager.interrupt_ai()

        self.asr_callback = ASRCallback(self)
        self.translator = TranslationRecognizerRealtime(
            model="gummy-realtime-v1",
            format="pcm",
            sample_rate=16000,
            transcription_enabled=True,
            translation_enabled=False,
            callback=self.asr_callback,
        )

    def init_audio(self):
        # 初始化音频设备
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=3200
        )

    def start(self):
        # 启动系统
        print("启动语音对话系统...")
        self.running = True
        self.translator.start()
        self.asr_thread.start()
        self.detection_thread.start()
        print("系统已准备就绪，可以开始对话")

    def stop(self):
        # 停止系统
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.mic:
            self.mic.terminate()
        self.translator.stop()
        if self.current_speech_process:
            self.interrupt_ai()
        print("对话系统已关闭")

    def asr_process_loop(self):
        # 持续处理音频数据
        while self.running:
            try:
                data = self.stream.read(3200, exception_on_overflow=False)
                self.audio_buffer.put(data)
                self.translator.send_audio_frame(data)
            except Exception as e:
                print(f"处理音频数据错误: {e}")
                time.sleep(0.1)
                break

    def detect_user_speech(self):
        # 检测用户是否开始说话
        print("检测用户语音线程已启动")
        silence_threshold = 300  # 静音阈值，需根据实际环境调整
        silence_frames = 0
        talking_frames = 0

        while self.running:
            try:
                if self.audio_buffer.empty():
                    time.sleep(0.1)
                    continue

                audio_data = self.audio_buffer.get()
                volume = sum(abs(int.from_bytes(audio_data[i:i + 2], 'little', signed=True))
                             for i in range(0, len(audio_data), 2)) / (len(audio_data) / 2)
                print(f"<UNK>: {volume}")

                # 在detect_user_speech方法中
                if volume > silence_threshold:
                    talking_frames += 1
                    silence_frames = 0
                    if talking_frames > 3:
                        print(f"检测到用户说话，音量: {volume}, 当前状态: {self.state}")

                        if self.state == "ai_speaking":
                            print("检测到用户说话，打断AI...")
                            self.interrupt_ai()
                        self.state = "user_speaking"
                else:
                    silence_frames += 1
                    talking_frames = 0
                    if silence_frames > 20 and self.state == "user_speaking":
                        print(f"检测到用户停止说话，沉默帧数: {silence_frames}")
                        print(f"当前识别文本: '{self.recognized_text}'")
                        self.state = "idle"

                        if self.recognized_text:
                            print("处理识别到的文本...")
                            self.process_user_input(self.recognized_text)
                            self.recognized_text = ""

                time.sleep(0.05)
            except Exception as e:
                print(f"检测用户语音错误: {e}")
                time.sleep(0.1)

    def interrupt_ai(self):
        try:
            print("正在尝试停止播放器...")

            with self.buffer_thread_lock:
                self.buffer_thread_running = False

            self.player.stop()
            print("播放器已停止")
        except Exception as e:
            print(f"停止播放器时出错: {e}")

    def process_user_input(self, text):

        if self.state == "ai_speaking":
            self.interrupt_ai()
            self.player.__init__()
            self.state = "idle"
        # 处理用户输入并生成AI响应
        print(f'用户问题: {text},时间: {time.strftime("%Y%m%d_%H%M%S")}')

        # 这里应调用实际的AI大模型获取回复
        # 示例回复
        # ai_response = f"我收到了您的问题：{text}。这是AI的模拟回答，实际使用时应替换为大模型的响应。"
        ai_response = self.agentchat.send_message(text=text)
        # 使用TTS播放AI响应
        self.speak(ai_response, self.stream_voice)
        with open(f'./VoiceTextData/temp_{time.strftime("%Y%m%d_%H%M%S")}.txt', "a") as f:
            f.write(str({
                "user_input": text,
                "ai_response": ai_response
            }))

    def response_split(self, text):
        # 将AI响应文本分割成多段，避免一次性播放过长文本
        # 以文本的句号，问号等符号为分隔符，分割文本

        segments = re.split(r'(?<=[。！？.!?])', text)
        print("分割文本片段：", [str(i) for i in segments if i != ''])
        return [segment.strip() for segment in segments if segment != '']

    def speak_buffer(self, text):
        """
        分段处理并播放AI回应
        创建音频缓冲池，将长文本分割为多个短句，依次合成音频并播放
        """
        self.state = "ai_speaking"
        print(f"AI回答（stream）: {text}")

        # 创建音频文件队列

        # 使用锁确保线程安全
        with self.buffer_thread_lock:
            self.buffer_thread_running = True

        def audio_queue_add(segments, audio_queue):
            for segment in segments:
                if not self.buffer_thread_running:
                    print("音频播放被中断")
                    break

                try:
                    # 请求TTS API生成语音
                    response = requests.post(TTS_API_URL, json={
                        "text": segment,
                        "voice": "longxiang",
                        "model": "cosyvoice-v1"
                    })

                    if response.status_code == 200:
                        try:
                            # 解析API响应获取文件路径
                            response_data = response.json()
                            if "file_path" in response_data:
                                output_file = response_data["file_path"]
                            else:
                                # 如果响应不包含路径，保存为临时文件
                                output_file = f"./VoiceData/temp_{int(time.time())}.mp3"
                                with open(output_file, 'wb') as f:
                                    f.write(response.content)

                            # 将音频文件加入队列
                            audio_queue.put(output_file)
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
                        # 等待播放完成
                        while not self.player.is_complete() and self.buffer_thread_running:
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
                add_thread = threading.Thread(target=audio_queue_add, args=(segments, audio_queue))
                play_thread = threading.Thread(target=audio_queue_play, args=(audio_queue,))

                add_thread.daemon = True
                play_thread.daemon = True

                # 启动线程
                play_thread.start()  # 先启动播放线程
                add_thread.start()  # 再启动添加线程

                # 等待添加线程完成
                add_thread.join()

                # 等待队列中的所有音频播放完毕
                while not audio_queue.empty() and self.buffer_thread_running:
                    time.sleep(0.2)

                # 结束播放线程
                self.buffer_thread_running = False
            finally:
                with self.buffer_thread_lock:
                    if self.buffer_thread_running:  # 只有在没被中断的情况下才重置状态
                        self.state = "idle"
                        self.buffer_thread_running = False

        # 创建并启动音频处理线程
        with self.buffer_thread_lock:
            self.buffer_thread = threading.Thread(target=process_and_play)
            self.buffer_thread.daemon = True
            self.buffer_thread.start()

    def speak(self, text, stream=False):
        if not stream:
            # 合成并播放AI回应
            self.state = "ai_speaking"
            print(f"AI回答: {text}")

            try:
                # 请求TTS API生成语音
                response = requests.post(TTS_API_URL, json={
                    "text": text,
                    "voice": "longxiang",
                    "model": "cosyvoice-v2"
                })

                if response.status_code == 200:
                    try:
                        # 尝试解析JSON响应获取文件路径
                        response_data = response.json()
                        if "file_path" in response_data:
                            # 使用API返回的文件路径直接播放
                            output_file = response_data["file_path"]
                            self.player.play(output_file)
                            self.current_speech_process = None
                        else:
                            print("API响应中没有找到文件路径")
                    except ValueError:
                        # 如果响应不是JSON格式，说明是直接返回的音频数据，使用原来的方式处理
                        output_file = f"./VoiceData/temp_{int(time.time())}.mp3"
                        with open(output_file, 'wb') as f:
                            f.write(response.content)
                        self.player.play(output_file)
                        # 播放完成后删除临时文件
                        # os.remove(output_file)
                        self.current_speech_process = None

            except Exception as e:
                print(f"生成或播放语音时出错: {str(e)}")

            self.state = "idle"
        else:
            # 流式播放AI回应
            self.speak_buffer(text)


# 主程序
if __name__ == "__main__":
    # 确保API密钥已设置
    dashscope.api_key = "your-api-key"

    # 创建对话管理器
    manager = DialogueManager()

    try:
        command = input("输入'sm'启动流式对话系统")
        if command.lower() == 'sm':
            manager.stream_voice = True
        # 启动对话系统

        manager.start()

        # 保持程序运行
        while True:
            command = input("输入'q'退出系统,输入sp立即停止语音: ")
            if command.lower() == 'q':
                break
            elif command.lower() == 'sp':
                manager.interrupt_ai()
            elif command.lower() == 'enter':
                manager.process_user_input(manager.recognized_text)
            elif command.lower() == 'text':
                print(manager.recognized_text)
            else:

                #直接对话
                manager.process_user_input(command)
    except KeyboardInterrupt:
        print("检测到Ctrl+C，正在退出...")
    finally:
        # 关闭系统
        manager.stop()
