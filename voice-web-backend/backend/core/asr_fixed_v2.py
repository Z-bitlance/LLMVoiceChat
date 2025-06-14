import base64
import threading
import time
import queue
import os

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
        self.watchdog_thread = None

        self.asr_callback = None
        self.translator = None
        
        # 添加状态属性
        self.state = "idle"  # 可能的状态: idle, user_speaking, ai_speaking
        
        # 用于打断AI的方法，默认为空实现
        self.interrupt_ai = lambda: print("打断AI (未实现)")

        # 会话活跃度时间戳
        self.last_activity = time.time()
        
        # 创建音频缓冲区
        self.audio_buffer = queue.Queue()

        # 控制线程
        self.running = True
        
        # 初始化语音识别 (仅初始化，不启动服务)
        self.init_asr()

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
                    self.manager.last_activity = time.time()

                def on_close(self):
                    print("语音识别已关闭")
                    
                def on_event(self, request_id, transcription_result, translation_result, usage):
                    if transcription_result is not None:
                        self.manager.recognized_text = transcription_result.text
                        print(f"识别到: {self.manager.recognized_text}")
                        self.manager.last_activity = time.time()  # 更新活跃时间戳

                        # 如果AI正在说话，打断它
                        if self.manager.state == "ai_speaking":
                            self.manager.interrupt_ai()
                            
                def on_error(self, err):
                    print(f"ASR错误: {err}")

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
            
    def watchdog_loop(self):
        """
        看门狗线程：监控ASR服务状态，如果发生异常自动重新连接
        定期发送心跳包保持连接活跃
        """
        print("看门狗线程已启动")
        check_interval = 5  # 每5秒检查一次
        heartbeat_interval = 15  # 每15秒发送一次心跳
        reconnect_threshold = 60  # 如果超过60秒没有活动，尝试重连
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                time.sleep(check_interval)
                now = time.time()
                
                # 检查是否需要发送心跳
                if now - last_heartbeat > heartbeat_interval:
                    # 发送一个静音帧，保持会话活跃
                    print("发送心跳包...")
                    silent_frame = bytes(1600)  # 1600字节的静音数据
                    if hasattr(self, 'translator'):
                        try:
                            self.translator.send_audio_frame(silent_frame)
                            last_heartbeat = now
                        except Exception as e:
                            print(f"发送心跳失败: {e}")
                
                # 检查连接是否长时间无响应
                if now - self.last_activity > reconnect_threshold:
                    print(f"警告: ASR服务 {reconnect_threshold} 秒无响应，尝试重新连接...")
                    # 重新初始化连接
                    self.reconnect_asr()
                    last_heartbeat = now
                    self.last_activity = now
                
            except Exception as e:
                print(f"看门狗线程检测到错误: {e}")
                time.sleep(1)  # 出错后稍微等待
        
        print("看门狗线程已退出")
        
    def reconnect_asr(self):
        """重新连接ASR服务"""
        try:
            # 停止现有服务
            if hasattr(self, 'translator'):
                try:
                    self.translator.stop()
                except Exception as e:
                    print(f"停止旧连接时出错: {e}")
            
            # 重新初始化ASR
            print("重新初始化ASR服务...")
            if self.init_asr():
                # 启动服务
                self.translator.start()
                print("ASR服务已重新连接")
                return True
            return False
        except Exception as e:
            print(f"重新连接ASR服务失败: {e}")
            return False
    
    def start_asr(self):
        """启动语音识别服务"""
        if dashscope is None:
            print("无法启动语音识别: dashscope 模块未安装")
            return False
            
        try:
            # 检查API密钥是否设置
            if not dashscope.api_key:
                api_key = os.environ.get("DASHSCOPE_API_KEY")
                if api_key:
                    dashscope.api_key = api_key
                else:
                    print("错误: 未设置DashScope API密钥")
                    return False
            
            # 如果已经在运行中，尝试停止旧的服务
            if hasattr(self, 'translator'):
                try:
                    self.translator.stop()
                    print("已停止旧的ASR服务")
                except Exception as e:
                    print(f"警告: 停止旧服务时出错: {e}")
            
            # 重新初始化ASR
            if not self.init_asr():
                return False

            # 启动翻译器
            self.translator.start()
            
            # 更新活跃时间戳
            self.last_activity = time.time()

            # 关闭任何已存在的线程
            self.running = False
            if hasattr(self, 'asr_thread') and self.asr_thread and self.asr_thread.is_alive():
                try:
                    self.asr_thread.join(1.0)  # 等待线程结束，最多1秒
                except:
                    pass
            
            if hasattr(self, 'detection_thread') and self.detection_thread and self.detection_thread.is_alive():
                try:
                    self.detection_thread.join(1.0)
                except:
                    pass
                
            if hasattr(self, 'watchdog_thread') and self.watchdog_thread and self.watchdog_thread.is_alive():
                try:
                    self.watchdog_thread.join(1.0)
                except:
                    pass

            # 设置运行标志并启动新线程
            self.running = True
            
            # 启动处理线程
            self.asr_thread = threading.Thread(target=self.asr_process_loop)
            self.detection_thread = threading.Thread(target=self.detect_user_speech)
            self.watchdog_thread = threading.Thread(target=self.watchdog_loop)

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
            # 先标记停止线程
            self.running = False
            
            # 停止翻译器
            if hasattr(self, 'translator'):
                try:
                    self.translator.stop()
                except Exception as e:
                    print(f"停止翻译器时出错: {e}")
            
            # 等待线程结束
            if hasattr(self, 'asr_thread') and self.asr_thread:
                try:
                    self.asr_thread.join(2.0)  # 等待至多2秒
                except:
                    pass
            
            if hasattr(self, 'detection_thread') and self.detection_thread:
                try:
                    self.detection_thread.join(2.0)
                except:
                    pass
                
            if hasattr(self, 'watchdog_thread') and self.watchdog_thread:
                try:
                    self.watchdog_thread.join(2.0)
                except:
                    pass
                
            print("语音识别服务已停止")
            return True
        except Exception as e:
            print(f"停止语音识别服务失败: {e}")
            return False

    def asr_process_loop(self):
        """持续处理音频数据"""
        print("音频处理线程已启动")
        error_count = 0
        max_errors = 5  # 最多允许连续5个错误
        
        while self.running:
            try:
                if self.audio_buffer.empty():
                    time.sleep(0.1)
                    continue

                data = self.audio_buffer.get()
                self.translator.send_audio_frame(data)
                error_count = 0  # 成功发送，重置错误计数
            except Exception as e:
                error_count += 1
                print(f"处理音频数据错误 ({error_count}/{max_errors}): {e}")
                
                if error_count >= max_errors:
                    print("连续错误过多，尝试重新连接...")
                    self.reconnect_asr()
                    error_count = 0
                    
                time.sleep(0.5)  # 出错后稍微等待
            
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
                
                # 计算音量
                try:
                    volume = sum(abs(int.from_bytes(audio_data[i:i + 2], 'little', signed=True))
                                for i in range(0, min(len(audio_data), 1600), 2)) / (min(len(audio_data), 1600) / 2)
                except:
                    # 如果无法计算音量（可能是心跳包），则使用最低音量
                    volume = 0

                # 根据音量判断用户是否在说话
                if volume > silence_threshold:
                    talking_frames += 1
                    silence_frames = 0
                    if talking_frames > 3:  # 连续3帧以上有声音才认为是说话开始
                        if self.state != "user_speaking":
                            print(f"检测到用户说话，音量: {volume}")
                            self.state = "user_speaking"
                            self.last_activity = time.time()  # 更新活跃时间戳
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
                time.sleep(0.5)
        
        print("检测用户语音线程已退出")

    def process_audio(self, audio_data):
        """处理从前端发送的音频数据"""
        try:
            # 将Base64编码的音频转换为二进制
            binary_audio = base64.b64decode(audio_data)

            # 加入音频缓冲区
            self.audio_buffer.put(binary_audio)
            
            # 更新活跃时间戳
            self.last_activity = time.time()

            # 如果ASR服务未启动，则尝试启动
            if not hasattr(self, 'translator') or not hasattr(self, 'asr_thread') or not self.asr_thread or not self.asr_thread.is_alive():
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
    
    # 创建退出事件
    exit_event = threading.Event()

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
            
        # 创建一个后台线程检查系统状态
        def status_checker():
            while not exit_event.is_set():
                # 每分钟打印一次状态信息
                time.sleep(60)
                if not exit_event.is_set():
                    now = time.time()
                    idle_time = now - manager.last_activity
                    print(f"系统状态: 最后活动 {int(idle_time)} 秒前，当前状态: {manager.state}")
        
        status_thread = threading.Thread(target=status_checker)
        status_thread.daemon = True
        status_thread.start()
            
        # 保持程序运行
        print("输入'q'退出系统, 输入'sp'停止语音识别, 输入'st'启动语音识别:")
        while True:
            command = input("> ")
            if command.lower() == 'q':
                print("正在退出系统...")
                exit_event.set()
                break
            elif command.lower() == 'sp':
                manager.stop_asr()
                print("语音识别已停止，输入'st'重新启动语音识别")
            elif command.lower() == 'st':
                manager.start_asr()
                print("语音识别已重新启动")
            elif command.lower() == 'text':
                print(f"当前识别文本: {manager.recognized_text}")
            elif command.lower() == 'status':
                now = time.time()
                idle_time = now - manager.last_activity
                print(f"系统状态: 最后活动 {int(idle_time)} 秒前，当前状态: {manager.state}")
            elif command.lower() == 'reconnect':
                print("手动尝试重新连接...")
                manager.reconnect_asr()
                
    except KeyboardInterrupt:
        print("\n检测到Ctrl+C，正在退出...")
        exit_event.set()
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("正在关闭ASR系统...")
        # 关闭系统
        if 'manager' in locals():
            manager.stop_asr()
        print("ASR系统已关闭")
