import os
import sys
import time
from src.flight_search import FlightSearch
from src.data_manager import DataManager
from src.notifier import LineNotifier

# 強制將 stdout 編碼設定為 utf-8 以支援繁體中文輸出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 設定區塊 ---
ORIGIN = "TPE"  # 台北出發
# 想要追蹤的目的地清單 (福岡, 札幌, 羽田, 成田)
DESTINATIONS = ["FUK", "CTS", "HND", "NRT"] 
# 各目的地期望買到的絕對低價 (台幣)
ABSOLUTE_THRESHOLDS = {
    "FUK": 8500,
    "CTS": 16000,
    "HND": 11000,
    "NRT": 10000
}
# --- 設定區塊 ---

def main():
    print("✈️ 開始執行機票價格追蹤...")
    searcher = FlightSearch()
    manager = DataManager()
    notifier = LineNotifier()

    for dest in DESTINATIONS:
        print(f"🔍 正在搜尋 {ORIGIN} 到 {dest} 的機票...")
        # 尋找未來 6 個月，停留 5-8 天的直飛機票
        flight_data = searcher.search_cheap_flights(
            origin=ORIGIN, 
            destination=dest, 
            months_ahead=6, 
            nights_from=5, 
            nights_to=8
        )

        if flight_data:
            current_price = flight_data["price"]
            print(f"👉 找到 {dest} 的最便宜價格: {current_price} TWD")
            
            # 取得該目的地的期望低價
            abs_threshold = ABSOLUTE_THRESHOLDS.get(dest, 3000)
            
            # 評估是否需要發送通知
            eval_result = manager.evaluate_price(
                destination=dest, 
                current_price=current_price, 
                absolute_threshold=abs_threshold
            )


            if eval_result:
                print(f"🔔 觸發通知條件: {eval_result['reason']}")
                notifier.format_and_send(flight_data, eval_result)
            else:
                print("💤 價格未達通知標準或為首次紀錄，僅更新歷史資料。")
        else:
            print(f"❌ 找不到符合條件的航班 ({dest})，可能 API 發生錯誤或無直飛航班。")

        # 稍微暫停避免觸發 API Rate Limit (次數限制)
        time.sleep(2)
        print("-" * 30)
        
    print("✅ 全部搜尋執行完畢！")

if __name__ == "__main__":
    main()
