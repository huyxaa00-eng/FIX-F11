import os
import re
import requests
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# Đã điền sẵn Token và Secret của bạn
LINE_CHANNEL_ACCESS_TOKEN = "ncim2CWvpmksOVNLAID+DspMKIC97Mcobc+p883QRJ0rYXfijKg/VXw5lpgf2nNqZWNtztsY/2G1QvqgckLaKetyivU12X1/O+ItkVYp6KWMW++8RR/q2lFI/asIEgcRAlVGW27R4afwgm29tP+7+QdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "d651dbbf5854a6cb29bb6a5a6c476476"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def simple_translate(text, target_lang):
  """Hàm dịch thuật sử dụng endpoint gtx của Google Translate"""
  try:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text}
    response = requests.get(url, params=params, timeout=5)
    if response.status_code == 200:
      res_json = response.json()
      translated_text = "".join([item[0] for item in res_json[0] if item[0]])
      return translated_text if translated_text else text
  except Exception as e:
    print(f"Lỗi dịch thuật: {e}")
  return text


@app.route("/callback", methods=["POST"])
def callback():
  signature = request.headers.get("X-Line-Signature", "")
  body = request.get_data(as_text=True)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)
  except Exception as e:
    print(f"Lỗi callback: {e}")
  return "OK", 200


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_text = event.message.text.strip()
  print(f"Nhận tin nhắn gốc: {user_text}")

  # Kiểm tra lệnh fixip / status
  if user_text.lower() in ["fixip", "status"]:
    translated = "🌐 Bot dịch thuật đang hoạt động ổn định trên Render!"
  else:
    # Tự động nhận diện chữ Trung Quốc để dịch qua lại (Việt <-> Trung Phồn Thể)
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', user_text))
    target_lang = "vi" if has_chinese else "zh-TW"
    
    # Thực hiện dịch
    translated = simple_translate(user_text, target_lang)

  print(f"Kết quả gửi đi: {translated}")

  # Trả kết quả đã dịch về lại LINE
  line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text=translated)
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
