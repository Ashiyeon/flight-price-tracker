import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
LINE_PUSH_API = "https://api.line.me/v2/bot/message/push"

class LineNotifier:
    def __init__(self):
        self.token = LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = LINE_USER_ID
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def send_notification(self, message: str) -> bool:
        if not self.token or not self.user_id:
            print("LINE 憑證未設定 (LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID)，略過通知發送。")
            return False

        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            response = requests.post(
                LINE_PUSH_API, 
                headers=self.headers, 
                data=json.dumps(payload)
            )
            response.raise_for_status()
            print("✅ 通知已成功透過 Messaging API 發送至 LINE！")
            return True
        except Exception as e:
            print(f"發送 LINE 通知時發生錯誤: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"錯誤詳情: {e.response.text}")
            return False

    def format_and_send(self, flight_data: dict, evaluation_result: dict):
        """
        將機票資訊與評估結果格式化成 LINE 訊息並發送。
        """
        msg = f"{evaluation_result['type']} {evaluation_result['reason']}\n"
        msg += "-" * 20 + "\n"
        msg += f"✈️ 目的地：{flight_data['destination']}\n"
        msg += f"💰 價格：{flight_data['price']} {flight_data['currency']}\n"
        msg += f"📅 去程：{flight_data['departure_date']}\n"
        msg += f"📅 回程：{flight_data['return_date']}\n"
        msg += f"🏢 航空：{', '.join(set(flight_data.get('airlines', ['未知'])) or ['未知'])}\n"
        msg += f"🔗 訂票連結：{flight_data.get('link', 'N/A')}\n"

        self.send_notification(msg)
