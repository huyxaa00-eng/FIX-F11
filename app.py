import os
import requests
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# Thay thế các token của LINE bot vào đây hoặc dùng biến môi trường
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN"
)
LINE_CHANNEL_SECRET = os.environ.get(
    "LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET"
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def simple_translate(text, target_lang):
  """Hàm dịch thuật sử dụng endpoint gtx của Google Translate để tránh rate-limit"""
  try:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text}
    response = requests.get(url, params=params, timeout=5)
    if response.status_code == 200:
      res_json = response.json()
      # Nối các đoạn văn bản đã dịch lại với nhau
      translated_text = "".join([item[0] for item in res_json[0] if item[0]])
      return translated_text
  except Exception as e:
    print(f"Lỗi dịch thuật: {e}")
  return text  # Nếu lỗi thì trả về nguyên bản


@app.route("/callback", methods=["POST"])
def callback():
  signature = request.headers["X-Line-Signature"]
  body = request.get_data(as_text=True)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)
  return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_text = event.message.text
  print(f"Nhận tin nhắn: {user_text}")

  # Tự động phát hiện ký tự tiếng Trung (\u4e00 - \u9fff) để chuyển đổi ngôn ngữ mục tiêu
  has_chinese = any("\u4e00" <= char <= "\u9fff" for char in user_text)
  target_lang = "vi" if has_chinese else "zh-TW"

  # Thực hiện dịch thuật
  translated = simple_translate(user_text, target_lang)

  # Xác định ID nguồn gửi (chat cá nhân, nhóm hay phòng)
  source_id = event.source.user_id
  if event.source.type == "group":
    source_id = event.source.group_id
  elif event.source.type == "room":
    source_id = event.source.room_id

  # Gửi kết quả ĐÃ DỊCH về LINE
  line_bot_api.push_message(
      source_id, TextSendMessage(text=translated)
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
