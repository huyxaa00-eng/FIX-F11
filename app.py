import os
import requests
from flask import Flask, request as req, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi('NOdW9CbDw92yYUx61TeF5HgPL/7atOYtizFu/hP8e8JaUiHDN6r9Nq6Wa6tPs4HuZWNtztsY/2G1QvqgckLaKetyivU12X1/O+ItkVYp6KW65e5VlpjQsAtbeayn37mcH8/ZOnyJ+4nQPQfDcAqFZwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('d651dbbf5854a6cb29bb6a5a6c476476')

def simple_translate(text, target_lang):
    try:
        # Sử dụng API dịch công khai ổn định, không bị chặn IP
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params, timeout=5)
        res_json = response.json()
        translated_text = "".join([item[0] for item in res_json[0] if item[0]])
        return translated_text
    except Exception as e:
        print(f"Lỗi dịch API: {e}")
        return text

@app.route("/callback", methods=['POST'])
def callback():
    signature = req.headers['X-Line-Signature']
    body = req.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    print(f"Nhận tin nhắn: {user_text}")
    
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_text)
    target_lang = 'vi' if has_chinese else 'zh-TW'
    
    translated = simple_translate(user_text, target_lang)

    source_id = event.source.user_id
    if event.source.type == 'group':
        source_id = event.source.group_id
    elif event.source.type == 'room':
        source_id = event.source.room_id

    line_bot_api.push_message(
        source_id,
        TextSendMessage(text=translated or user_text)
    )

if __name__ == "__main__":
    app.run(port=5000)
