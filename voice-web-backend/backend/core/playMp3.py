import sys
import os
import subprocess
import time
import threading
from playsound import playsound
import argparse

from arcade import load_sound, play_sound, stop_sound

# sound = load_sound("1.mp3")
# # 开始播放
# player = play_sound(sound)
# # 停止播放
# stop_sound(player)


class MP3Player:
    """MP3播放器类，支持多种播放方式和中断功能"""

    def __init__(self):
        self.playing = False
        self.play_thread = None
        self.process = None
        self.pygame_initialized = False

        self.sound=None
        self.arcade_player=None

    def is_complete(self):

        if self.sound:
            return self.sound.is_complete(self.arcade_player)
        else:
            return True

    def play(self, file_path, method='arcade'):
        """播放MP3文件

        Args:
            file_path: MP3文件路径
            method: 播放方式，可选 'playsound', 'subprocess', 'pygame'

        Returns:
            bool: 是否成功启动播放
        """
        if not os.path.exists(file_path):
            print(f"错误: 文件 '{file_path}' 不存在")
            return False

        # 如果已经在播放，先停止当前播放
        if self.playing:
            self.stop()

        self.playing = True
        if method == 'arcade':
            self.sound = load_sound(file_path)
            # 开始播放
            self.arcade_player = play_sound(self.sound)
            #返回音频长度
            return self.sound,self.arcade_player

        elif method == 'playsound':
            self.play_thread = threading.Thread(target=self._play_with_playsound, args=(file_path,))
            self.play_thread.daemon = True
            self.play_thread.start()

        elif method == 'subprocess':
            self._play_with_subprocess_windows(file_path)
        elif method == 'pygame':
            self._play_with_pygame(file_path)
        else:
            print(f"错误: 不支持的播放方式 '{method}'")
            self.playing = False
            return False

        return True

    def stop(self):
        """停止当前播放"""

        self.playing = False

        # 停止arcade播放
        if self.arcade_player:

            stop_sound(self.arcade_player)
            self.arcade_player = None

        # 如果有播放线程，等待其结束
        if self.play_thread and self.play_thread.is_alive():
            # print("正在停止播放...")
            self.play_thread.join(1.0)
            self.play_thread = None

        # 停止subprocess进程
        if self.process:
            try:
                self.process.terminate()
                self.process = None
            except:
                pass

        # 停止pygame播放
        if self.pygame_initialized:
            try:
                import pygame
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                self.pygame_initialized = False
            except:
                pass

        print("播放已停止")

    def _play_with_playsound(self, file_path):
        """使用playsound库播放MP3文件"""
        try:
            print(f"正在播放: {file_path}")
            playsound(file_path)
            if self.playing:  # 如果不是被中断的
                print("播放完成")
        except Exception as e:
            print(f"播放出错: {str(e)}")
        finally:
            self.playing = False

    def _play_with_subprocess_windows(self, file_path):
        """在Windows上使用subprocess播放MP3文件"""
        try:
            print(f"正在播放: {file_path}")
            self.process = subprocess.Popen(["start", file_path], shell=True)

            # 创建监控线程
            self.play_thread = threading.Thread(target=self._subprocess_monitor)
            self.play_thread.daemon = True
            self.play_thread.start()
            return True
        except Exception as e:
            print(f"播放出错: {str(e)}")
            self.playing = False
            return False

    def _subprocess_monitor(self):
        """监控subprocess播放状态的线程函数"""
        try:
            if self.process:
                self.process.wait()
                if self.playing:  # 如果不是被中断的
                    print("播放完成")
        except:
            pass
        finally:
            self.playing = False

    def _play_with_pygame(self, file_path):
        """使用pygame库播放MP3文件"""
        try:
            import pygame
            pygame.mixer.init()
            self.pygame_initialized = True
            print(f"正在播放: {file_path}")
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # 启动监听线程
            self.play_thread = threading.Thread(target=self._pygame_monitor)
            self.play_thread.daemon = True
            self.play_thread.start()
            return True
        except Exception as e:
            print(f"播放出错: {str(e)}")
            self.playing = False
            self.pygame_initialized = False
            return False

    def _pygame_monitor(self):
        """监控pygame播放状态的线程函数"""
        import pygame
        try:
            # 等待播放完成或被中断
            while self.playing and pygame.mixer.music.get_busy():
                time.sleep(0.5)

            if self.playing:  # 播放自然结束
                print("播放完成")
        except:
            pass
        finally:
            self.playing = False

    def is_playing(self):
        """返回当前是否正在播放"""
        return self.playing


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='播放MP3文件')
    parser.add_argument('file', nargs='?', help='MP3文件路径')
    parser.add_argument('--method', choices=['playsound', 'subprocess', 'pygame'],
                        default='playsound', help='播放方式 (默认: playsound)')
    args = parser.parse_args()

    # 获取文件路径
    if args.file:
        file_path = args.file
    else:
        file_path = input("请输入MP3文件路径: ")

    # 创建播放器并开始播放
    player = MP3Player()
    success = player.play(file_path, args.method)

    if not success:
        return

    print("按 'q' 键停止播放，按 'Ctrl+C' 退出程序")
    try:
        while player.is_playing():
            cmd = input()
            if cmd.lower() == 'q':
                player.stop()
                time.sleep(10)
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        player.stop()
        print("\n程序已终止")


if __name__ == "__main__":
    main()