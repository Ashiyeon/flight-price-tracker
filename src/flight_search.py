import os
import requests
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "fly-scraper.p.rapidapi.com"
RAPIDAPI_ENDPOINT = "https://fly-scraper.p.rapidapi.com/v2/flights/search-roundtrip"

class FlightSearch:
    def __init__(self):
        self.headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }

    def search_cheap_flights(self, origin: str, destination: str, months_ahead: int = 6, nights_from: int = 5, nights_to: int = 8, currency: str = "TWD") -> dict | None:
        """
        使用 Fly-Scraper API 搜尋機票。
        """
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        return_date = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")

        query = {
            "originSkyId": origin,
            "destinationSkyId": destination,
            "fromDate": departure_date,
            "toDate": return_date,
            "currency": currency
        }

        # 使用者指定的航空公司白名單 (中英文對照以應對不同 API 回傳結果)
        allowed_airlines = [
            "中華航空", "China Airlines",
            "日本航空", "Japan Airlines", "JAL",
            "台灣虎航", "Tigerair Taiwan", "Tigerair",
            "全日空", "全日空航空", "All Nippon Airways", "ANA",
            "長榮航空", "EVA Air",
            "國泰航空", "Cathay Pacific",
            "酷航", "Scoot",
            "樂桃航空", "Peach", "Peach Aviation"
        ]

        try:
            print(f"DEBUG: 正在呼叫 Fly-Scraper API ({origin} -> {destination})...")
            response = requests.get(RAPIDAPI_ENDPOINT, headers=self.headers, params=query)
            
            if response.status_code != 200:
                print(f"API 錯誤: {response.status_code} - {response.text}")
                return None
            
            data = response.json()

            if "status" in data and data["status"] is False:
                print(f"API 回傳失敗訊息: {data.get('message', '未知錯誤')}")
                return None

            itineraries = data.get("data", {}).get("itineraries", [])
            if not itineraries:
                print(f"找不到從 {origin} 到 {destination} 的航班資料。")
                return None

            best_flight = None
            best_airlines = []

            # 遍歷航班，尋找完全符合白名單的最便宜機票
            for flight in itineraries:
                airlines_in_flight = []
                legs = flight.get("legs", [])
                
                # 收集這個航班的所有承運航空公司
                for leg in legs:
                    carriers = leg.get("carriers", {}).get("marketing", [])
                    for carrier in carriers:
                        airlines_in_flight.append(carrier.get("name", "未知航空"))
                
                # 檢查這個航班的所有航空公司是否都在我們的白名單中
                is_valid = True
                for al in airlines_in_flight:
                    # 使用部分比對，只要名稱中包含白名單的關鍵字即可 (不分大小寫)
                    if not any(allowed.lower() in al.lower() for allowed in allowed_airlines):
                        is_valid = False
                        break
                
                if is_valid:
                    best_flight = flight
                    best_airlines = list(set(airlines_in_flight))
                    break # 因為 itineraries 通常已由低價到高價排序，第一個找到的就是最便宜的

            if not best_flight:
                print(f"在 {origin} 到 {destination} 中，沒有找到符合指定航空公司的航班。")
                return None
            
            # 解析價格 - 處理多種可能格式
            raw_price = None
            price_data = best_flight.get("price", {})
            
            if isinstance(price_data, dict):
                # 優先使用 raw 數值
                raw_price = price_data.get("raw")
                if raw_price is None:
                    # 其次嘗試從 formatted 提取數字
                    formatted = price_data.get("formatted", "")
                    if formatted:
                        # 移除逗號和非數字字元 (保留小數點)
                        clean_price = re.sub(r'[^\d.]', '', formatted)
                        if clean_price:
                            raw_price = float(clean_price)
            else:
                raw_price = price_data

            # 確保價格是數字
            try:
                price = float(raw_price)
            except (ValueError, TypeError):
                print(f"無法解析價格: {raw_price}")
                return None

            # 處理多位數整數問題 (Fly-Scraper 某些回傳值會放大 1000 倍或更多)
            # 如果 TWD 價格超過 100 萬，極大機率是位數問題
            if price > 1000000:
                price = price / 1000
            elif price > 100000:
                price = price / 100

            # 提取航空公司
            airlines = []
            legs = best_flight.get("legs", [])
            for leg in legs:
                carriers = leg.get("carriers", {}).get("marketing", [])
                for carrier in carriers:
                    airlines.append(carrier.get("name", "未知航空"))
            
            if not airlines:
                airlines = ["多航空公司"]

            return {
                "destination": destination,
                "price": price,
                "currency": currency,
                "departure_date": best_flight.get("legs", [{}])[0].get("departure", departure_date).split("T")[0],
                "return_date": best_flight.get("legs", [{}, {}])[1].get("departure", return_date).split("T")[0] if len(legs) > 1 else "N/A",
                "airlines": list(set(airlines)),
                "link": f"https://www.google.com/flights?hl=zh-TW#flt={origin}.{destination}.{departure_date}*{destination}.{origin}.{return_date}"
            }

        except Exception as e:
            print(f"搜尋發生錯誤 ({destination}): {e}")
            return None
