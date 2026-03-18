import json
import os
from datetime import datetime

DATA_FILE = "data/price_history.json"

class DataManager:
    def __init__(self):
        self.data_file = DATA_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        # 確保 data 資料夾存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def load_data(self) -> dict:
        with open(self.data_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_data(self, data: dict):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def evaluate_price(self, trip_id: str, current_price: float, absolute_threshold: float = 8000, discount_threshold: float = 0.20) -> dict | None:
        """
        評估目前票價是否值得發送通知。
        使用 trip_id (例如: 東京賞櫻_NRT) 作為歷史紀錄的 Key，確保不同日期的行程分開計算。
        """
        # 強制將 current_price 轉為數字
        try:
            current_price = float(current_price)
        except (ValueError, TypeError):
            print(f"警告：價格無法轉換為數字: {current_price}")
            return None

        data = self.load_data()
        today = datetime.now().strftime("%Y-%m-%d")

        if trip_id not in data:
            data[trip_id] = {
                "historical_low": current_price,
                "history": {today: current_price}
            }
            self.save_data(data)
            return None # 第一次紀錄只建立基準，暫不發送通知

        trip_data = data[trip_id]
        
        # 讀取並轉換歷史價格，確保都是數字
        history = {}
        for k, v in trip_data.get("history", {}).items():
            try:
                history[k] = float(v)
            except:
                continue
        
        historical_low = float(trip_data.get("historical_low", float('inf')))

        notify_reason = None
        message_prefix = ""

        # 條件 1: 絕對低價 (例如低於 8000)
        if current_price <= absolute_threshold:
            notify_reason = f"低於您的期望值 ({absolute_threshold})"
            message_prefix = "🎯【期望低價】"

        # 條件 2: 特價/降價跳水 (計算過去 7 天平均)
        recent_prices = list(history.values())[-7:]
        if recent_prices:
            avg_price = sum(recent_prices) / len(recent_prices)
            # 跌幅超過 discount_threshold (例如 20%)
            if current_price <= avg_price * (1 - discount_threshold):
                 notify_reason = f"比近七天平均 ({avg_price:.0f}) 便宜超過 {discount_threshold*100:.0f}%！"
                 message_prefix = "🚨【特價降落】"

        # 條件 3: 歷史新低 (權重最高，會覆蓋前面的 Prefix)
        if current_price < historical_low:
            notify_reason = f"打破歷史新低！原最低價為 {historical_low}"
            message_prefix = "🌟【歷史新低】"
            trip_data["historical_low"] = current_price

        # 每日更新歷史紀錄
        history[today] = current_price
        trip_data["history"] = history
        self.save_data(data)

        if notify_reason:
            return {
                "type": message_prefix,
                "reason": notify_reason,
            }

        return None
