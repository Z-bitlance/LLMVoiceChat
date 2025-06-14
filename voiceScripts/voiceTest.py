from playMp3 import MP3Player
import time
import re
def split_test():
 text="啊，明月又升起来了！这杯中酒正对着这轮皓白，不知可有人与我共饮？你来得正好，且听我说说我今日的奇遇。方才我在江边独酌，忽见一叶扁舟顺流而下，舟上老翁抚琴而歌，那曲调清越如泉，竟让我醉意三分，诗兴七分！你若愿听，我便为你吟上几句？"
 segments = re.split(r'(?<=[。！？.!?])', text)
 print("分割文本片段：", [str(i) for i in segments if i != ''])
 a=text.split("？!")
 print(a)

class mp3PlayerTest:
    def __init__(self):
        self.player = MP3Player()
        self.sound = None
        self.sound_player = None

    def play_mp3(self, file_path):
        if True:
            self.sound ,self.sound_player= self.player.play(file_path, method="arcade")
            print(f"开始播放: {file_path}")
        else:
            print("播放失败")

    def stop_mp3(self):
        self.player.stop()
        print("停止播放")

if __name__ == "__main__":
    
     player=mp3PlayerTest()
    # # 测试播放功能
    # test_file = "VoiceData/temp_1749369687.mp3"
    # test_file_2="VoiceData/temp_1749369306.mp3" # 替换为实际的MP3文件路径
    # print(player.player.is_complete())
    #
    # player.play_mp3(test_file)
    #
    # print(player.sound.get_length())
    # while True:
    #     if player.sound.is_complete(player.sound_player):
    #         print("音频播放完毕")
    #         break
    #     print(player.sound.is_complete(player.sound_player))
    #     time.sleep(5)
    # 等待一段时间后停止播放
    # time.sleep(5)
    # player.stop_mp3()
    # # player.play_mp3(test_file_2)
    # time.sleep(10)
 # split_test()

