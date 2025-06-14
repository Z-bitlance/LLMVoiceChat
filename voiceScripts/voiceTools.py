import os
import time
import uuid
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import ffmpeg
import moviepy.editor as mp
from scipy.signal import butter, lfilter

# 尝试导入 spleeter, 如果失败则提供备用方案
SPLEETER_AVAILABLE = False
try:
    from spleeter.separator import Separator
    SPLEETER_AVAILABLE = True
except ImportError:
    # spleeter 不可用，可能是 Python 版本不兼容
    pass

class AudioVideoTools:
    """
    音频视频工具类，用于对音频和视频进行简单的剪辑和处理操作。
    支持的功能包括：剪切、拼接、转换格式、提取音频、音频过滤等。
    """
    
    def __init__(self, output_dir='../VoiceData'):
        """
        初始化音视频工具类
        
        参数:
            output_dir (str): 输出目录路径
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _generate_output_path(self, suffix):
        """生成唯一的输出文件路径"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"temp_{timestamp}.{suffix}"
        return os.path.join(self.output_dir, filename)
    
    def _generate_uuid_path(self, suffix):
        """生成基于UUID的唯一输出文件路径"""
        filename = f"{uuid.uuid4()}.{suffix}"
        return os.path.join(self.output_dir, filename)
    
    # ====== 音频处理功能 ======
    
    def convert_audio_format(self, input_path, output_format='mp3'):
        """
        转换音频格式
        
        参数:
            input_path (str): 输入音频文件路径
            output_format (str): 目标格式 (mp3, wav, ogg等)
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=output_format)
        return output_path
    
    def trim_audio(self, input_path, start_time, end_time, output_format='mp3'):
        """
        剪切音频文件
        
        参数:
            input_path (str): 输入音频文件路径
            start_time (float): 开始时间（秒）
            end_time (float): 结束时间（秒）
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        audio = AudioSegment.from_file(input_path)
        
        # 转换为毫秒
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        # 剪切音频
        trimmed_audio = audio[start_ms:end_ms]
        trimmed_audio.export(output_path, format=output_format)
        
        return output_path
    
    def concatenate_audio(self, input_paths, output_format='mp3'):
        """
        拼接多个音频文件
        
        参数:
            input_paths (list): 输入音频文件路径列表
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 创建一个空的音频段
        combined = AudioSegment.empty()
        
        # 依次添加每个音频文件
        for path in input_paths:
            audio = AudioSegment.from_file(path)
            combined += audio
            
        # 导出拼接后的音频
        combined.export(output_path, format=output_format)
        
        return output_path
    
    def adjust_volume(self, input_path, gain_db, output_format='mp3'):
        """
        调整音频音量
        
        参数:
            input_path (str): 输入音频文件路径
            gain_db (float): 增益值（分贝），正值增大音量，负值减小音量
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        audio = AudioSegment.from_file(input_path)
        
        # 调整音量
        adjusted_audio = audio + gain_db
        
        # 导出调整后的音频
        adjusted_audio.export(output_path, format=output_format)
        
        return output_path
    
    def apply_fade(self, input_path, fade_in_ms=0, fade_out_ms=0, output_format='mp3'):
        """
        应用淡入淡出效果
        
        参数:
            input_path (str): 输入音频文件路径
            fade_in_ms (int): 淡入时长（毫秒）
            fade_out_ms (int): 淡出时长（毫秒）
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        audio = AudioSegment.from_file(input_path)
        
        # 应用淡入淡出效果
        processed_audio = audio
        if fade_in_ms > 0:
            processed_audio = processed_audio.fade_in(fade_in_ms)
        if fade_out_ms > 0:
            processed_audio = processed_audio.fade_out(fade_out_ms)
        
        # 导出处理后的音频
        processed_audio.export(output_path, format=output_format)
        
        return output_path
      def extract_vocals(self, input_path, output_format='mp3'):
        """
        从音频中提取人声部分（使用Spleeter库或备用方案）
        
        参数:
            input_path (str): 输入音频文件路径
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径（人声部分）
        """
        if not SPLEETER_AVAILABLE:
            print("警告：Spleeter 库不可用，无法进行高质量的人声分离")
            print("原因：当前 Python 版本不兼容 (需要 Python 3.7-3.10)")
            print("使用备用人声提取方法（简单高通滤波）")
            return self._extract_vocals_fallback(input_path, output_format)
            
        # 创建临时目录
        temp_dir = os.path.join(self.output_dir, 'temp_spleeter')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 使用Spleeter进行人声分离
            separator = Separator('spleeter:2stems')  # 2stems模式：vocals和accompaniment
            separator.separate_to_file(input_path, temp_dir)
            
            # 提取处理后的文件路径
            input_filename = os.path.basename(input_path).split('.')[0]
            vocals_path = os.path.join(temp_dir, input_filename, 'vocals.wav')
            
            # 转换为所需格式
            output_path = self._generate_output_path(output_format)
            vocals = AudioSegment.from_file(vocals_path)
            vocals.export(output_path, format=output_format)
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return output_path
        except Exception as e:
            print(f"Spleeter处理失败: {str(e)}")
            print("使用备用人声提取方法")
            return self._extract_vocals_fallback(input_path, output_format)
    
    def _extract_vocals_fallback(self, input_path, output_format='mp3'):
        """
        人声提取的备用方法（使用简单的高通滤波）
        
        参数:
            input_path (str): 输入音频文件路径
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载音频
        y, sr = librosa.load(input_path, sr=None)
        
        # 应用高通滤波器提取人声频率（简单的频域分离）
        def butter_highpass(cutoff, fs, order=5):
            nyq = 0.5 * fs
            normal_cutoff = cutoff / nyq
            b, a = butter(order, normal_cutoff, btype='high', analog=False)
            return b, a

        def butter_highpass_filter(data, cutoff, fs, order=5):
            b, a = butter_highpass(cutoff, fs, order=order)
            y = lfilter(b, a, data)
            return y
        
        # 人声通常在较高频率范围
        cutoff = 180  # 高通滤波截止频率
        filtered_audio = butter_highpass_filter(y, cutoff, sr)
        
        # 保存处理后的音频
        sf.write(output_path, filtered_audio, sr)
        
        return output_path
      def remove_vocals(self, input_path, output_format='mp3'):
        """
        从音频中去除人声（保留伴奏）
        
        参数:
            input_path (str): 输入音频文件路径
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径（伴奏部分）
        """
        if not SPLEETER_AVAILABLE:
            print("警告：Spleeter 库不可用，无法进行高质量的人声分离")
            print("原因：当前 Python 版本不兼容 (需要 Python 3.7-3.10)")
            print("使用备用伴奏提取方法（简单低通滤波）")
            return self._remove_vocals_fallback(input_path, output_format)
            
        # 创建临时目录
        temp_dir = os.path.join(self.output_dir, 'temp_spleeter')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 使用Spleeter进行人声分离
            separator = Separator('spleeter:2stems')  # 2stems模式：vocals和accompaniment
            separator.separate_to_file(input_path, temp_dir)
            
            # 提取处理后的文件路径
            input_filename = os.path.basename(input_path).split('.')[0]
            accompaniment_path = os.path.join(temp_dir, input_filename, 'accompaniment.wav')
            
            # 转换为所需格式
            output_path = self._generate_output_path(output_format)
            accompaniment = AudioSegment.from_file(accompaniment_path)
            accompaniment.export(output_path, format=output_format)
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return output_path
        except Exception as e:
            print(f"Spleeter处理失败: {str(e)}")
            print("使用备用伴奏提取方法")
            return self._remove_vocals_fallback(input_path, output_format)
    
    def _remove_vocals_fallback(self, input_path, output_format='mp3'):
        """
        去除人声的备用方法（使用简单的低通滤波）
        
        参数:
            input_path (str): 输入音频文件路径
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载音频
        y, sr = librosa.load(input_path, sr=None)
        
        # 应用低通滤波器提取伴奏（简单的频域分离）
        def butter_lowpass(cutoff, fs, order=5):
            nyq = 0.5 * fs
            normal_cutoff = cutoff / nyq
            b, a = butter(order, normal_cutoff, btype='low', analog=False)
            return b, a

        def butter_lowpass_filter(data, cutoff, fs, order=5):
            b, a = butter_lowpass(cutoff, fs, order=order)
            y = lfilter(b, a, data)
            return y
        
        # 伴奏通常在较低频率范围
        cutoff = 180  # 低通滤波截止频率
        filtered_audio = butter_lowpass_filter(y, cutoff, sr)
        
        # 保存处理后的音频
        sf.write(output_path, filtered_audio, sr)
        
        return output_path
    
    def noise_reduction(self, input_path, output_format='mp3'):
        """
        简单的音频降噪处理
        
        参数:
            input_path (str): 输入音频文件路径
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载音频
        y, sr = librosa.load(input_path, sr=None)
        
        # 简单的降噪处理（低通滤波器）
        def butter_lowpass(cutoff, fs, order=5):
            nyq = 0.5 * fs
            normal_cutoff = cutoff / nyq
            b, a = butter(order, normal_cutoff, btype='low', analog=False)
            return b, a

        def butter_lowpass_filter(data, cutoff, fs, order=5):
            b, a = butter_lowpass(cutoff, fs, order=order)
            y = lfilter(b, a, data)
            return y
        
        # 应用低通滤波器
        cutoff = 2000  # 截止频率
        filtered_audio = butter_lowpass_filter(y, cutoff, sr)
        
        # 保存处理后的音频
        sf.write(output_path, filtered_audio, sr)
        
        return output_path
    
    def change_speed(self, input_path, speed_factor=1.0, output_format='mp3'):
        """
        改变音频播放速度（不改变音高）
        
        参数:
            input_path (str): 输入音频文件路径
            speed_factor (float): 速度因子，>1加速，<1减速
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 使用ffmpeg处理音频速度
        try:
            (
                ffmpeg
                .input(input_path)
                .filter('atempo', speed_factor)
                .output(output_path)
                .run(quiet=True, overwrite_output=True)
            )
        except ffmpeg.Error as e:
            print(f"FFmpeg处理错误: {e.stderr.decode()}")
            return None
            
        return output_path
    
    def pitch_shift(self, input_path, semitones=0, output_format='mp3'):
        """
        改变音频的音高
        
        参数:
            input_path (str): 输入音频文件路径
            semitones (int): 音高变化的半音数，正值提高音调，负值降低音调
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载音频
        y, sr = librosa.load(input_path, sr=None)
        
        # 应用音高变换
        shifted_y = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
        
        # 保存处理后的音频
        sf.write(output_path, shifted_y, sr)
        
        return output_path
    
    # ====== 视频处理功能 ======
    
    def extract_audio_from_video(self, video_path, output_format='mp3'):
        """
        从视频中提取音频
        
        参数:
            video_path (str): 输入视频文件路径
            output_format (str): 输出音频格式
            
        返回:
            str: 输出音频文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 使用moviepy提取音频
        video = mp.VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_path)
        
        # 关闭视频文件
        video.close()
        
        return output_path
    
    def trim_video(self, input_path, start_time, end_time, output_format='mp4'):
        """
        剪切视频片段
        
        参数:
            input_path (str): 输入视频文件路径
            start_time (float): 开始时间（秒）
            end_time (float): 结束时间（秒）
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 使用moviepy剪切视频
        video = mp.VideoFileClip(input_path)
        trimmed_video = video.subclip(start_time, end_time)
        trimmed_video.write_videofile(output_path)
        
        # 关闭视频文件
        video.close()
        trimmed_video.close()
        
        return output_path
    
    def concatenate_videos(self, input_paths, output_format='mp4'):
        """
        拼接多个视频文件
        
        参数:
            input_paths (list): 输入视频文件路径列表
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载所有视频剪辑
        clips = [mp.VideoFileClip(path) for path in input_paths]
        
        # 拼接视频
        final_clip = mp.concatenate_videoclips(clips)
        
        # 写入输出文件
        final_clip.write_videofile(output_path)
        
        # 关闭所有视频文件
        for clip in clips:
            clip.close()
        final_clip.close()
        
        return output_path
    
    def add_audio_to_video(self, video_path, audio_path, output_format='mp4'):
        """
        为视频添加音频（替换原有音频）
        
        参数:
            video_path (str): 输入视频文件路径
            audio_path (str): 输入音频文件路径
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载视频和音频
        video = mp.VideoFileClip(video_path)
        audio = mp.AudioFileClip(audio_path)
        
        # 根据视频长度截取或循环音频
        video_duration = video.duration
        if audio.duration > video_duration:
            # 音频较长，截取与视频等长的部分
            audio = audio.subclip(0, video_duration)
        elif audio.duration < video_duration:
            # 音频较短，循环播放以填充视频
            repeats = int(np.ceil(video_duration / audio.duration))
            audio = mp.concatenate_audioclips([audio] * repeats).subclip(0, video_duration)
        
        # 设置视频的音频
        video_with_audio = video.set_audio(audio)
        
        # 写入输出文件
        video_with_audio.write_videofile(output_path)
        
        # 关闭所有文件
        video.close()
        audio.close()
        video_with_audio.close()
        
        return output_path
    
    def change_video_speed(self, input_path, speed_factor=1.0, output_format='mp4'):
        """
        改变视频播放速度
        
        参数:
            input_path (str): 输入视频文件路径
            speed_factor (float): 速度因子，>1加速，<1减速
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载视频
        video = mp.VideoFileClip(input_path)
        
        # 改变速度
        fast_video = video.fx(mp.vfx.speedx, speed_factor)
        
        # 写入输出文件
        fast_video.write_videofile(output_path)
        
        # 关闭所有文件
        video.close()
        fast_video.close()
        
        return output_path
    
    def add_text_overlay(self, video_path, text, position=('center', 'bottom'), 
                        fontsize=24, color='white', start_time=0, end_time=None,
                        output_format='mp4'):
        """
        为视频添加文字叠加层
        
        参数:
            video_path (str): 输入视频文件路径
            text (str): 要添加的文本
            position (tuple): 文本位置，可以是(x,y)坐标或('center','bottom')等
            fontsize (int): 字体大小
            color (str): 字体颜色
            start_time (float): 文字开始时间（秒）
            end_time (float): 文字结束时间（秒），None表示到视频结束
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 加载视频
        video = mp.VideoFileClip(video_path)
        
        # 如果没有指定结束时间，则默认到视频结束
        if end_time is None:
            end_time = video.duration
        
        # 创建文本剪辑
        txt_clip = mp.TextClip(text, fontsize=fontsize, color=color)
        txt_clip = txt_clip.set_position(position).set_start(start_time).set_end(end_time)
        
        # 叠加文本
        final_clip = mp.CompositeVideoClip([video, txt_clip])
        
        # 写入输出文件
        final_clip.write_videofile(output_path)
        
        # 关闭所有文件
        video.close()
        txt_clip.close()
        final_clip.close()
        
        return output_path
    
    def create_video_from_images(self, image_paths, duration_per_image=2, output_format='mp4'):
        """
        从多张图片创建幻灯片视频
        
        参数:
            image_paths (list): 输入图片文件路径列表
            duration_per_image (float): 每张图片的持续时间（秒）
            output_format (str): 输出格式
            
        返回:
            str: 输出文件路径
        """
        output_path = self._generate_output_path(output_format)
        
        # 创建剪辑列表
        clips = [mp.ImageClip(img_path).set_duration(duration_per_image) for img_path in image_paths]
        
        # 拼接所有图片剪辑
        concat_clip = mp.concatenate_videoclips(clips, method="compose")
        
        # 写入输出文件
        concat_clip.write_videofile(output_path, fps=24)
        
        # 关闭所有文件
        for clip in clips:
            clip.close()
        concat_clip.close()
        
        return output_path

# 使用示例
if __name__ == "__main__":
    tools = AudioVideoTools()
    
    # 音频处理示例
    # 剪切音频
    trimmed_audio = tools.trim_audio("D:/pythonprojects/pythonProject/spider/bilibili/bili_data/bilibili_video_20250612_230524.mp3", 10, 30)
    print(f"剪切后的音频保存在: {trimmed_audio}")
    
    # 拼接音频
    # concat_audio = tools.concatenate_audio(["../VoiceData/audio1.mp3", "../VoiceData/audio2.mp3"])
    # print(f"拼接后的音频保存在: {concat_audio}")
    #
    # # 提取人声
    # vocals = tools.extract_vocals("../VoiceData/song.mp3")
    # print(f"提取的人声保存在: {vocals}")
    #
    # # 视频处理示例
    # # 从视频提取音频
    # audio = tools.extract_audio_from_video("../VoiceData/video.mp4")
    # print(f"提取的音频保存在: {audio}")
    #
    # # 视频剪切
    # trimmed_video = tools.trim_video("../VoiceData/video.mp4", 5, 15)
    # print(f"剪切后的视频保存在: {trimmed_video}")