import os
import sys
import time
from datetime import datetime, timedelta
from src.flight_search import FlightSearch
from src.data_manager import DataManager
from src.notifier import LineNotifier

# 強制將 stdout 編碼設定為 utf-8 以支援繁體中文輸出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 設定區塊 ---
ORIGIN = "TPE"  # 台北出發

# 您可以自由在這裡新增、修改想要追蹤的行程
# - dest: 目的地 (例如 NRT, FUK)
# - depart_date: 去程日期 (YYYY-MM-DD)。如果設為 None，系統會自動搜尋 30 天後的機票。
# - return_date: 回程日期 (YYYY-MM-DD)。如果設為 None，系統會自動搜尋 35 天後的機票。
# - threshold: 期望低價 (低於此價格會立刻通知)
# - label: 行程標籤 (會顯示在通知上，也用來區分歷史紀錄)
TRACKED_TRIPS = [
    {
        "label": "雙十東京羽田", 
        "dest": "HND", 
        "depart_date": "2026-10-07", 
        "return_date": "2026-10-11", 
        "threshold": 30000
    },
    {
        "label": "雙十東京成田", 
        "dest": "NRT", 
        "depart_date": "2026-10-07", 
        "return_date": "2026-10-11", 
        "threshold": 11000
    },
    {
        "label": "光復東京羽田", 
        "dest": "HND", 
        "depart_date": "2026-10-22", 
        "return_date": "2026-10-26", 
        "threshold": 18000
    },
    {
        "label": "光復東京成田", 
        "dest": "NRT", 
        "depart_date": "2026-10-22", 
        "return_date": "2026-10-26", 
        "threshold": 12000
    },
    {
        "label": "石垣島", 
        "dest": "ISG", 
        "depart_date": None, 
        "return_date": None,
        "threshold": 8000
    },
    {
        "label": "宮古島 (星宇)", 
        "dest": "SHI", 
        "depart_date": "2026-07-18", 
        "return_date": "2026-07-20",
        "threshold": 10000
    }
]
# --- 設定區塊 ---

def main():
    print("✈️ 開始執行機票價格追蹤 (自訂日期版)...")
    searcher = FlightSearch()
    manager = DataManager()
    notifier = LineNotifier()

    for trip in TRACKED_TRIPS:
        dest = trip["dest"]
        label = trip["label"]
        threshold = trip["threshold"]
        
        # 決定日期
        depart = trip["depart_date"] or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        ret = trip["return_date"] or (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
        
        # 產生唯一識別碼 (例如: 端午東京_NRT_2026-05-29)
        trip_id = f"{label}_{dest}_{depart}"

        print(f"🔍 正在搜尋 【{label}】 {ORIGIN} 到 {dest} ({depart} ~ {ret})...")
        
        flight_data = searcher.search_cheap_flights(
            origin=ORIGIN, 
            destination=dest, 
            departure_date=depart,
            return_date=ret
        )

        if flight_data:
            current_price = flight_data["price"]
            print(f"👉 找到最便宜價格: {current_price} TWD")
            
            # 評估是否需要發送通知
            eval_result = manager.evaluate_price(
                trip_id=trip_id, 
                current_price=current_price, 
                absolute_threshold=threshold
            )
            if eval_result:
                print(f"🔔 觸發通知條件: {eval_result['reason']}")
                notifier.format_and_send(flight_data, eval_result, label=label)
            else:
                print("💤 價格未達通知標準或為首次紀錄，僅更新歷史資料。")
        else:
            print(f"❌ 找不到符合條件的航班 ({dest})，可能該日期無直飛或無指定航空。")

        # 稍微暫停避免觸發 API Rate Limit
        time.sleep(2)
        print("-" * 30)
        
    print("✅ 全部搜尋執行完畢！")

if __name__ == "__main__":
    main()
