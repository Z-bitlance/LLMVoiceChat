import base64
import threading
import time
import queue

try:
    import dashscope
except ImportError:
    print("警告: 未找到 dashscope 模块，请确保已安装: pip install dashscope")
    dashscope = None

class ASRmanager:
    def __init__(self):
        self.recognized_text = None
        self.detection_thread = None
        self.asr_thread = None

        self.asr_callback = None
        self.translator = None
        
        # 添加状态属性
        self.state = "idle"  # 可能的状态: idle, user_speaking, ai_speaking
        
        # 用于打断AI的方法，默认为空实现
        self.interrupt_ai = lambda: print("打断AI (未实现)")

        # 初始化语音识别
        self.init_asr()
        self.audio_buffer = queue.Queue()

        # 控制线程
        self.running = True
        
        # 注意: 线程在start_asr中启动，而不是在这里
        self.asr_thread = None
        self.detection_thread = None

    def init_asr(self):
        """初始化语音识别"""
        if dashscope is None:
            print("无法初始化语音识别: dashscope 模块未安装")
            return False
            
        try:
            # 配置ASR回调
            class ASRCallback(dashscope.audio.asr.TranslationRecognizerCallback):
                def __init__(self, manager):
                    self.manager = manager

                def on_open(self):
                    print("语音识别已启动")

                def on_close(self):
                    print("语音识别已关闭")
                    
                def on_event(self, request_id, transcription_result, translation_result, usage):
                    if transcription_result is not None:
                        self.manager.recognized_text = transcription_result.text
                        print(f"识别到: {self.manager.recognized_text}")

                        # 如果AI正在说话，打断它
                        if self.manager.state == "ai_speaking":
                            self.manager.interrupt_ai()

            self.asr_callback = ASRCallback(self)
            self.translator = dashscope.audio.asr.TranslationRecognizerRealtime(
                model="gummy-realtime-v1",
                format="pcm",
                sample_rate=16000,
                transcription_enabled=True,
                translation_enabled=False,
                callback=self.asr_callback,
            )

            # 初始化运行标志
            self.running = True
            return True
        except Exception as e:
            print(f"初始化语音识别失败: {e}")
            return False
    def start_asr(self):
        """启动语音识别服务"""
        if dashscope is None:
            print("无法启动语音识别: dashscope 模块未安装")
            return False
            
        try:
            # 如果已经在运行中，则不重新启动
            if hasattr(self, 'translator') and hasattr(self, 'asr_thread') and self.asr_thread.is_alive():
                print("ASR服务已在运行中")
                return True
                
            # 如果存在旧的translator但未正确关闭，先停止它
            if hasattr(self, 'translator'):
                try:
                    self.translator.stop()
                except:
                    pass
                    
            # 重新初始化ASR
            if not self.init_asr():
                return False

            self.translator.start()

            # 设置运行标志
            self.running = True
            
            # 启动处理线程
            self.asr_thread = threading.Thread(target=self.asr_process_loop)
            self.detection_thread = threading.Thread(target=self.detect_user_speech)
            self.watchdog_thread = threading.Thread(target=self.watchdog_loop)  # 添加看门狗线程

            # 设置为非守护线程，这样主线程退出时不会自动终止这些线程
            self.asr_thread.daemon = False
            self.detection_thread.daemon = False
            self.watchdog_thread.daemon = False

            self.asr_thread.start()
            self.detection_thread.start()
            self.watchdog_thread.start()

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
                if self.audio_buffer.empty():
                    time.sleep(0.1)
                    continue

                data = self.audio_buffer.get()
                self.translator.send_audio_frame(data)
            except Exception as e:
                print(f"处理音频数据错误: {e}")
                time.sleep(0.1)
        print("音频处理线程已退出")

    def detect_user_speech(self):
        """检测用户是否开始说话"""
        print("检测用户语音线程已启动")
        silence_threshold = 5  # 静音阈值，需根据实际环境调整
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
                print(f"<UNK>: {audio_data}")

                # 根据音量判断用户是否在说话
                if volume > silence_threshold:
                    talking_frames += 1
                    silence_frames = 0
                    if talking_frames > 3:  # 连续3帧以上有声音才认为是说话开始
                        print(f"检测到用户说话，音量: {volume}")
                        self.state = "user_speaking"
                else:
                    silence_frames += 1
                    talking_frames = 0

                    # 如果用户停止讲话超过设定的时间，并且之前状态是用户讲话
                    if silence_frames > silence_frames_limit and self.state == "user_speaking":
                        print(f"检测到用户停止说话，沉默帧数: {silence_frames}")
                        print(f"当前识别文本: '{self.recognized_text}'")
                        self.state = "idle"

                time.sleep(0.05)
            except Exception as e:
                print(f"检测用户语音错误: {e}")
                time.sleep(0.1)
        
        print("检测用户语音线程已退出")

    def process_audio(self, audio_data):
        """处理从前端发送的音频数据"""
        try:
            # 将Base64编码的音频转换为二进制
            binary_audio = base64.b64decode(audio_data)

            # 加入音频缓冲区
            self.audio_buffer.put(binary_audio)

            # 如果ASR服务未启动，则尝试启动
            if not hasattr(self, 'translator') or not hasattr(self, 'asr_thread') or not self.asr_thread.is_alive():
                self.start_asr()

            return {
                "status": "success",
                "message": "音频数据已接收",
                "recognized_text": self.recognized_text
            }
        except Exception as e:
            print(f"处理音频数据错误: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if dashscope is None:
        print("错误: 找不到 dashscope 模块，请先安装: pip install dashscope")
        exit(1)
        
    # 确保API密钥已设置
    dashscope.api_key = "sk-d03c4fe2b7424948a9e3fbc698e35f6f"  # 注意：实际应用中应从环境变量或配置文件读取

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
        print("输入'q'退出系统, 输入'sp'停止语音识别, 输入'st'启动语音识别:")
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
