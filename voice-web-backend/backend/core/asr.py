import base64
from tkinter.font import names

import dashscope
import threading
import time
import pyaudio
import queue


class ASRmanager:
    def __init__(self):
        self.recognized_text = None
        self.detection_thread = None
        self.asr_thread = None

        self.asr_callback = None
        self.translator = None

        self.stream=None
        self.mic=None
        
        # 添加状态属性
        self.state = "idle"  # 可能的状态: idle, user_speaking, ai_speaking

        self.init_asr()
        self.audio_buffer = queue.Queue()

        # 控制线程
        self.running = True
        self.asr_thread = threading.Thread(target=self.asr_process_loop)
        self.detection_thread = threading.Thread(target=self.detect_user_speech)

    # def init_audio(self):
    #     # 初始化音频设备
    #     self.mic = pyaudio.PyAudio()
    #     self.stream = self.mic.open(
    #         format=pyaudio.paInt16,
    #         channels=1,
    #         rate=16000,
    #         input=True,
    #         frames_per_buffer=3200
    #     )

    def init_asr(self):
        """初始化语音识别"""
        try:
            # 配置ASR回调
            class ASRCallback(dashscope.audio.asr.TranslationRecognizerCallback):
                def __init__(self, manager):
                    self.manager = manager

                def on_open(self):
                    print("语音识别已启动")
                    self.manager.mic = pyaudio.PyAudio()
                    self.manager.stream = self.manager.mic.open(
                        format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=3200
                    )
                def on_close(self):
                    print("语音识别已关闭")
                    self.manager.stream.stop_stream()
                    self.manager.stream.close()
                    self.manager.mic.terminate()
                    self.manager.stream = None
                    self.manager.mic = None
                    
                def on_event(self, request_id, transcription_result, translation_result, usage):
                    if transcription_result is not None:
                        self.manager.recognized_text = transcription_result.text
                        print(f"识别到: {self.manager.recognized_text}")

                        # 如果AI正在说话，打断它
                        # if hasattr(self.manager, 'interrupt_ai') and self.manager.state == "ai_speaking":
                        #     self.manager.interrupt_ai()

            self.asr_callback = ASRCallback(self)
            self.translator = dashscope.audio.asr.TranslationRecognizerRealtime(
                model="gummy-realtime-v1",
                format="pcm",
                sample_rate=16000,
                transcription_enabled=True,
                translation_enabled=False,
                callback=self.asr_callback,
            )

            # 初始化运行标志和线程
            self.running = True
            return True
        except Exception as e:
            print(f"初始化语音识别失败: {e}")
            return False

    def start_asr(self):
        """启动语音识别服务"""
        try:
            if not hasattr(self, 'translator'):
                if not self.init_asr():
                    return False

            self.translator.start()

            # 启动处理线程
            self.asr_thread = threading.Thread(target=self.asr_process_loop)
            self.detection_thread = threading.Thread(target=self.detect_user_speech)

            self.asr_thread.daemon = True
            self.detection_thread.daemon = True

            self.asr_thread.start()
            self.detection_thread.start()

            print("语音识别服务已启动")
            return True
        except Exception as e:
            print(f"启动语音识别服务失败: {e}")
            return False

    def stop_asr(self):
        """停止语音识别服务"""
        try:
            self.running = False
            if hasattr(self, 'translator'):
                self.translator.stop()
            print("语音识别服务已停止")
            return True
        except Exception as e:
            print(f"停止语音识别服务失败: {e}")
            return False

    def asr_process_loop(self):
        """持续处理音频数据"""
        print("音频处理线程已启动")
        while self.running:
            try:
                # if self.stream is None or self.mic is None:
                #     self.init_asr()
                #
                # if self.audio_buffer.empty():
                #     time.sleep(0.5)
                #     continue

                data = self.stream.read(3200, exception_on_overflow=False)
                self.audio_buffer.put(data)
                self.translator.send_audio_frame(data)

            except Exception as e:
                print(f"处理音频数据错误: {e}")
                time.sleep(0.1)

    def detect_user_speech(self):
        """检测用户是否开始说话"""
        print("检测用户语音线程已启动")
        silence_threshold = 500  # 静音阈值，需根据实际环境调整
        silence_frames = 0
        talking_frames = 0
        silence_duration = 1.0  # 多少秒的沉默后处理识别文本
        silence_frames_limit = int(silence_duration / 0.05)  # 以50ms为单位的帧数

        while self.running:
            try:
                if self.audio_buffer.empty():
                    time.sleep(0.1)
                    continue

                audio_data = self.audio_buffer.get()
                volume = sum(abs(int.from_bytes(audio_data[i:i + 2], 'little', signed=True))
                             for i in range(0, len(audio_data), 2)) / (len(audio_data) / 2)
                print(f"<UNK>: {volume}")

                # 根据音量判断用户是否在说话
                if volume > silence_threshold:
                    talking_frames += 1
                    silence_frames = 0
                    if talking_frames > 3:  # 连续3帧以上有声音才认为是说话开始
                        print(f"检测到用户说话，音量: {volume}")

                        # if self.state == "ai_speaking":
                        #     print("检测到用户说话，打断AI...")
                        #     self.interrupt_ai()
                        # self.state = "user_speaking"
                else:
                    silence_frames += 1
                    talking_frames = 0

                    # 如果用户停止讲话超过设定的时间，并且之前状态是用户讲话
                    if silence_frames > silence_frames_limit:
                        print(f"检测到用户停止说话，沉默帧数: {silence_frames}")
                        print(f"当前识别文本: '{self.recognized_text}'")

                        # 如果有识别到的文本，则处理
                        if self.recognized_text and len(self.recognized_text.strip()) > 0:
                            print("处理识别到的文本...")
                            return self.recognized_text

                time.sleep(0.05)
            except Exception as e:
                print(f"检测用户语音错误: {e}")
                time.sleep(0.1)
        return None

    def process_one_time_audio(self, audio_data):
        """处理一次性发送的音频数据进行识别

        Args:
            audio_data: Base64编码的音频数据

        Returns:
            dict: 包含识别状态和识别文本的字典
        """
        try:
            print("处理一次性音频数据...:", audio_data[:50])
            # 将Base64编码的音频转换为二进制
            binary_audio = base64.b64decode(audio_data)

            # 创建存储结果的容器和事件
            result = {"text": ""}
            recognition_done = threading.Event()

            def process_audio_thread():
                try:
                    # 创建临时回调
                    class TempCallback(dashscope.audio.asr.TranslationRecognizerCallback):
                        def __init__(self):
                            self.collected_text = ""

                        def on_event(self, request_id, transcription_result, translation_result, usage):
                            if transcription_result is not None:
                                self.collected_text = transcription_result.text
                                print(f"临时识别器识别到: {self.collected_text}")

                        def on_error(self, err):
                            print(f"临时识别器错误: {err}")
                            recognition_done.set()

                        def on_close(self):
                            recognition_done.set()

                    callback = TempCallback()

                    # 创建临时翻译器
                    translator = dashscope.audio.asr.TranslationRecognizerRealtime(
                        model="gummy-realtime-v1",
                        format="pcm",
                        sample_rate=16000,
                        transcription_enabled=True,
                        translation_enabled=False,
                        callback=callback,
                    )

                    # 开始识别
                    translator.start()
                    translator.send_audio_frame(binary_audio)

                    # 等待一段时间以确保识别完成
                    time.sleep(2.0)

                    # 保存结果并清理
                    result["text"] = callback.collected_text
                    translator.stop()

                except Exception as e:
                    print(f"临时音频识别线程错误: {e}")
                finally:
                    # 标记识别完成
                    recognition_done.set()

            # 启动临时识别线程
            thread = threading.Thread(target=process_audio_thread)
            thread.daemon = True
            thread.start()

            # 等待识别完成或超时
            if not recognition_done.wait(timeout=5.0):
                print("一次性音频识别超时")

            return {
                "status": "success",
                "message": "一次性音频数据已处理",
                "recognized_text": result["text"]
            }
        except Exception as e:
            print(f"处理一次性音频数据错误: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # 确保API密钥已设置
    dashscope.api_key = "sk-d03c4fe2b7424948a9e3fbc698e35f6f"

    try:
        # 创建对话管理器
        manager = ASRmanager()
        print("创建ASR管理器成功")
        
        # 启动对话系统
        success = manager.start_asr()
        if success:
            print("ASR系统启动成功，程序正在运行...")
        else:
            print("ASR系统启动失败")
            exit(1)
            
        # 保持程序运行
        print("输入'q'退出系统, 输入'sp'停止语音识别:")
        while True:
            command = input("> ")
            if command.lower() == 'q':
                print("正在退出系统...")
                break
            elif command.lower() == 'sp':
                manager.stop_asr()
                print("语音识别已停止，输入'st'重新启动语音识别")
            elif command.lower() == 'st':
                manager.start_asr()
                print("语音识别已重新启动")
            elif command.lower() == 'text':
                print(f"当前识别文本: {manager.recognized_text}")
                
    except KeyboardInterrupt:
        print("\n检测到Ctrl+C，正在退出...")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("正在关闭ASR系统...")
        # 关闭系统
        if 'manager' in locals():
            manager.stop_asr()
        print("ASR系统已关闭")