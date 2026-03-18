import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class LineService:
    """專門處理 LINE 發送的類別"""
    def __init__(self):
        self.token = LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = LINE_USER_ID
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def send_notification(self, message: str) -> bool:
        if not self.token or not self.user_id:
            return False

        payload = {
            "to": self.user_id,
            "messages": [{"type": "text", "text": message}]
        }

        try:
            response = requests.post("https://api.line.me/v2/bot/message/push", headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"LINE 發送失敗: {e}")
            return False

class TelegramService:
    """專門處理 Telegram 發送的類別"""
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID

    def send_notification(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Telegram 發送失敗: {e}")
            return False

class LineNotifier:
    """
    這是一個門面類別 (Facade)，
    為了保持與 main.py 的相容性，它會同時發送到所有平台。
    """
    def __init__(self):
        self.line = LineService()
        self.telegram = TelegramService()

    def send_all(self, message: str):
        """同時發送到 LINE 和 Telegram"""
        line_res = self.line.send_notification(message)
        tele_res = self.telegram.send_notification(message)
        
        if line_res: print("✅ LINE 通知已發送")
        if tele_res: print("✅ Telegram 通知已發送")
        return line_res or tele_res

    def format_and_send(self, flight_data: dict, evaluation_result: dict, label: str = ""):
        # 如果有標籤，就放在最前面
        label_text = f"【{label}】\n" if label else ""
        msg = f"{label_text}{evaluation_result['type']} {evaluation_result['reason']}\n"
        msg += "-" * 20 + "\n"
        msg += f"✈️ 目的地：{flight_data['destination']}\n"
        msg += f"💰 價格：{flight_data['price']} {flight_data['currency']}\n"
        msg += f"📅 去程：{flight_data['departure_date']}\n"
        msg += f"📅 回程：{flight_data['return_date']}\n"
        msg += f"🏢 航空：{', '.join(set(flight_data.get('airlines', ['未知'])))}\n"
        msg += f"🔗 訂票連結：{flight_data.get('link', 'N/A')}\n"

        self.send_all(msg)
