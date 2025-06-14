import os
import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer
from dashscope.audio.tts_v2 import VoiceEnrollmentService
import time

Api_key = 'sk-d03c4fe2b7424948a9e3fbc698e35f6f'  # 如果您没有配置环境变量，请在此处用您的API-KEY进行替换

# object,url
# archive_yunli_24.wav,https://voice-training-data.oss-cn-beijing.aliyuncs.com/archive_yunli_24.wav?Expires=1749730696&OSSAccessKeyId=TMP.3KsPDe8bkfz4iXfFJDPaEckPJ4Z6irKw9RwUmGVHQzqcZBxMdvmwNHu45aH5hW2WDLSadYneZe8g6g3sYkRpox63XTES3S&Signature=3dCEtUW1XcpjHX2SNF08UJD0ZiA%3D

def copyVoiceByMp3(voiceUrl):
     url = "https://voice-training-data.oss-cn-beijing.aliyuncs.com/archive_yunli_24.wav?Expires=1749730696&OSSAccessKeyId=TMP.3KsPDe8bkfz4iXfFJDPaEckPJ4Z6irKw9RwUmGVHQzqcZBxMdvmwNHu45aH5hW2WDLSadYneZe8g6g3sYkRpox63XTES3S&Signature=3dCEtUW1XcpjHX2SNF08UJD0ZiA%3D"  # 请按实际情况进行替换
     prefix = 'prefix'
     target_model = "cosyvoice-v2"

     dashscope.api_key=Api_key

     # 创建语音注册服务实例
     service = VoiceEnrollmentService()

     # 调用create_voice方法复刻声音，并生成voice_id
     # 避免频繁调用 create_voice 方法。每次调用都会创建新音色，每个阿里云主账号最多可复刻 1000 个音色，超额时请删除不用的音色或申请扩容。
     voice_id = service.create_voice(target_model=target_model, prefix=prefix, url=voiceUrl)
     print("requestId: ", service.get_last_request_id())
     print(f"your voice id is {voice_id}")

     # 使用复刻的声音进行语音合成
     synthesizer = SpeechSynthesizer(model=target_model, voice=voice_id)
     audio = synthesizer.call("今天天气怎么样,要出去走走吗？")
     print("requestId: ", synthesizer.get_last_request_id())

     # 将合成的音频文件保存到本地文件
     with open("output1.mp3", "wb") as f:
         f.write(audio)

def TTSWithCopiedVoice(voiceId,text):

     target_model = "cosyvoice-v2"
     # 使用复刻的声音进行语音合成
     synthesizer = SpeechSynthesizer(model=target_model, voice=voiceId)
     audio = synthesizer.call(text if text is not None else "今天天气怎么样,要出去走走吗？")
     print("requestId: ", synthesizer.get_last_request_id())

     # 将合成的音频文件保存到本地文件
     with open(f'output_{time.strftime("%Y%m%d_%H%M%S")}.mp3', "wb") as f:
         f.write(audio)





def listCopiedVoices():

     dashscope.api_key = Api_key  # 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
     prefix = 'prefix' # 请按实际情况进行替换

     # 创建语音注册服务实例
     service = VoiceEnrollmentService()

     voices = service.list_voices(prefix=prefix, page_index=0, page_size=10)
     print("request id为：", service.get_last_request_id())
     print(f"查询到的音色为：{voices}")


def updateVoice(voiceUrl):

     dashscope.api_key = Api_key  # 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
     url = "https://your-audio-file-url"  # 请按实际情况进行替换
     voice_id = 'cosyvoice-v2-prefix-xxx' # 请按实际情况进行替换

     # 创建语音注册服务实例
     service = VoiceEnrollmentService()

     service.update_voice(voice_id=voice_id, url=voiceUrl)
     print("request id为：", service.get_last_request_id())

# {'gmt_create': '2025-06-13 13:53:34', 'voice_id': 'cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6', 'gmt_modified': '2025-06-13 13:53:41', 'status': 'OK'}]

# url="https://voice-training-data.oss-cn-beijing.aliyuncs.com/bilibili_video_20250612_230524_%E4%B8%9C%E9%9B%AA%E8%8E%B2.mp3?Expires=1749794547&OSSAccessKeyId=TMP.3KoEB3jNfuGxPxcdrmYozJ9cjXTcPsJfxXH2VgUyfRwa9o3ApMEcirJFMCdmBREefrGg8216stAvb6PmLEHkANv4AGKfKe&Signature=R4NIN3ugTT5%2FALBM3oKdgWM427s%3D"
# copyVoiceByMp3(url)

def main():
     voiceId="cosyvoice-v2-prefix-e929f25649664a16adaf04fc563870f6"
     text="哎，你是不是脑子有什么大病啊！？"
     TTSWithCopiedVoice(voiceId, text)

listCopiedVoices()