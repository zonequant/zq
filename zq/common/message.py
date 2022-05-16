"https://open.feishu.cn/open-apis/bot/hook/b1aa39a0d98b43448cb76b18a2c4c6f7"

import requests
import json
from loguru import logger as log

class Feishu():
    def __init__(self,bot):
            self.url="https://open.feishu.cn/open-apis/bot/hook/"+bot
    def send(self,title, text):
        data = json.dumps({"title" : title, "text" : text}, ensure_ascii= False)
        byte_data =  data.encode('utf-8')
        result = requests.post(self.url,byte_data)


class Dingtalk():
    def __init__(self,token):
        self.url=f"https://oapi.dingtalk.com/robot/send?access_token={token}"
    def send(self, text):
        data = json.dumps(text, ensure_ascii= False)
        byte_data =  data.encode('utf-8')
        head= {"Content-Type": "application/json"}
        result = requests.post(self.url,byte_data,headers=head)
        return result


if __name__ == "__main__":
    wx=Feishu("19479203478@chatroom")
    wx.send("test")
