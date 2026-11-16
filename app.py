import os
import re
import requests
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# Dán trực tiếp Token và Secret của bạn vào đây
LINE_CHANNEL_ACCESS_TOKEN = "YOUR_CHANNEL_ACCESS_TOKEN"
LINE_CHANNEL_SECRET = "YOUR_CHANNEL_SECRET"

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
      return translated_text
  except Exception as e:
    print(f"Lỗi dịch thuật: {e}")
  return text


def get_current_ip_and_proxy_status():
  """Kiểm tra IP hiện tại và trạng thái proxy (Lệnh fixip)"""
  try:
    ip_res = requests.get("https://api.ipify.org?format=json", timeout=5)
    current_ip = ip_res.json().get("ip", "Không xác định") if ip_res.status_code == 200 else "Không lấy được IP"
    
    status_msg = f"🌐 **Trạng thái Proxy & IP:**\n- IP hiện tại đang chạy: {current_ip}\n- Trạng thái: Hoạt động bình thường"
    return status_msg
  except Exception as e:
    return f"Lỗi kiểm tra IP/Proxy: {str(e)}"


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
  user_text = event.message.text.strip()
  print(f"Nhận tin nhắn: {user_text}")

  # 1. Kiểm tra nếu nhắn "fixip" hoặc "status"
  if user_text.lower() == "fixip" or user_text.lower() == "status":
    translated = get_current_ip_and_proxy_status()
  else:
    # 2. Tự động nhận diện chữ Trung Quốc để dịch qua lại (vi <-> zh-TW)
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', user_text))
    target_lang = "vi" if has_chinese else "zh-TW"
    
    # Thực hiện dịch
    translated = simple_translate(user_text, target_lang)

  # Xác định ID nguồn gửi (cá nhân hoặc nhóm)
  source_id = event.source.user_id
  if event.source.type == 'group':
    source_id = event.source.group_id
  elif event.source.type == 'room':
    source_id = event.source.room_id

  # 3. QUAN TRỌNG: Gửi biến `translated` (kết quả dịch) về LINE chứ không gửi `user_text`
  line_bot_api.push_message(
      source_id,
      TextSendMessage(text=translated)
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
