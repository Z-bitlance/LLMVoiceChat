import os
import time
from http import HTTPStatus
from dashscope import Application

app_id = ['5ffe587bb14941cda6012bffe3ac3f46', 'e2eed5eed7bb4fa8a75a7b4cfc8fb235']
character = {'nekogirl':'5ffe587bb14941cda6012bffe3ac3f46', 'libai': 'e2eed5eed7bb4fa8a75a7b4cfc8fb235'}


class AgentChat:
    def __init__(self, api_key="sk-d03c4fe2b7424948a9e3fbc698e35f6f",character_id="", character_name='nekogirl'):
        """初始化聊天代理

        Args:
            api_key: DashScope API密钥
            app_id: 应用ID
        """
        self.api_key = api_key
        self.app_id = character_id if character_id is not None else character[character_name] if character_name in character.keys() else app_id[0]  # 默认选择第一个角色
        self.session_id = None
        self.last_response = None  # 添加存储最后回复的属性

    def select_character(self, character_id):
        """选择角色

        Args:
            character_id: 角色ID
        """
        if character_id < len(app_id) and app_id[character_id] is not self.app_id:
            self.app_id = app_id[character_id]
            self.session_id = None  # 如果角色ID更改，重置会话ID

        print(f"已选择角色: {character[character_id] if character_id < len(character) else character[0]}")

    def send_message(self, text):
        """发送消息并获取响应

        Args:
            text: 用户输入的文本

        Returns:
            str: AI的响应文本
        """
        if self.session_id is None:
            # 首次对话，创建新会话
            response = Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=text
            )
            if response.status_code != HTTPStatus.OK:
                print(f'请求出错: code={response.status_code}, message={response.message}')
                self.last_response = f"请求错误: {response.message}"
                return self.last_response
            else:
                self.session_id = response.output.session_id
                self.last_response = response.output.text
                # print(f'请求成功: , message={response.output.text}')
                return self.last_response
        else:
            # 继续已有会话
            response = Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=text,
                session_id=self.session_id
            )

            if response.status_code != HTTPStatus.OK:
                print(f'请求出错: code={response.status_code}, message={response.message}')
                return f"请求错误: {response.message}"
            else:
                self.last_response = response.output.text
                # print(f'请求成功: , message={response.output.text}')
                return self.last_response

    def reset_session(self):
        """重置会话，开始新的对话"""
        self.session_id = None


# 保持向后兼容的全局函数
chat_session = None


def call_with_session(text: str = '你是谁？'):
    global chat_session
    print("chat_session: ", chat_session, '\n')
    if chat_session is None:
        response = Application.call(
            api_key="sk-d03c4fe2b7424948a9e3fbc698e35f6f",
            app_id='e2eed5eed7bb4fa8a75a7b4cfc8fb235',
            prompt=text,
        )

        if response.status_code != HTTPStatus.OK:
            print(f'request_id={response.request_id}')
            print(f'code={response.status_code}')
            print(f'message={response.message}')
            print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
            return response
        else:
            chat_session = response.output.session_id
            print('%s\n session_id=%s\n' % (response.output.text, response.output.session_id))
            return response.output.text
    else:
        responseNext = Application.call(
            api_key="sk-d03c4fe2b7424948a9e3fbc698e35f6f",
            app_id='e2eed5eed7bb4fa8a75a7b4cfc8fb235',
            prompt=text,
            session_id=chat_session
        )

        if responseNext.status_code != HTTPStatus.OK:
            print(f'request_id={responseNext.request_id}')
            print(f'code={responseNext.status_code}')
            print(f'message={responseNext.message}')
            print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
        else:
            print('%s\n session_id=%s\n' % (responseNext.output.text, responseNext.output.session_id))
            return responseNext.output.text


if __name__ == '__main__':
    # 使用新的类实现命令行交互
    agent = AgentChat()
    print("开始对话，输入'退出'结束")

    while True:
        user_input = input("请输入您的问题（或输入'退出'结束对话）：")
        if user_input.lower() == '退出':
            print("对话结束。")
            break
        else:
            print("请求成功，输出对话为：",agent.send_message(user_input),f'\n输出时间:{time.strftime("%Y%m%d_%H%M%S")}')
