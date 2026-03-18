import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

class FlightSearch:
    def __init__(self):
        self.api_key = SERPAPI_API_KEY
        if not self.api_key or self.api_key == "your_serpapi_key_here":
            print("⚠️ 請先在 .env 中設定 SERPAPI_API_KEY")

    def search_cheap_flights(self, origin: str, destination: str, departure_date: str, return_date: str, currency: str = "TWD") -> dict | None:
        """
        使用 SerpApi (Google Flights) 搜尋指定日期的直飛特價機票。
        """
        if not self.api_key or self.api_key == "your_serpapi_key_here":
            return None

        # 使用者指定的航空公司白名單
        allowed_airlines = [
            "中華航空", "China Airlines",
            "日本航空", "Japan Airlines", "JAL",
            "台灣虎航", "Tigerair Taiwan", "Tigerair",
            "全日空", "全日空航空", "All Nippon Airways", "ANA",
            "長榮航空", "EVA Air",
            "國泰航空", "Cathay Pacific",
            "酷航", "Scoot",
            "樂桃航空", "Peach", "Peach Aviation",
            "星宇航空", "Starlux Airlines", "Starlux",
            # 支援日本國內線轉機 (針對離島)
            "日本跨洋航空", "Japan Transocean Air", "JTA",
            "琉球空中通勤", "Ryukyu Air Commuter", "RAC",
            "全日空之翼", "ANA Wings"
        ]

        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "return_date": return_date,
            "currency": currency,
            "hl": "zh-TW",
            "type": "1", # 1: 來回 (Round trip)
            "api_key": self.api_key
        }

        try:
            print(f"DEBUG: 正在呼叫 SerpApi (Google Flights) ({origin} -> {destination})...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Google Flights 會回傳 best_flights (最佳航班) 和 other_flights (其他航班)
            flights_list = data.get("best_flights", []) + data.get("other_flights", [])
            
            if not flights_list:
                print(f"找不到從 {origin} 到 {destination} 的航班資料。")
                return None

            best_flight = None
            best_airlines = []
            best_price = float('inf')

            for option in flights_list:
                price = option.get("price")
                if price is None:
                    continue
                    
                flights = option.get("flights", [])
                
                # 檢查是否為直飛 (如果每個航段的 flights 數量為 1)
                # 針對離島，我們可能需要放寬這個條件。這裡先以「總航班數越少越好」且「必須符合白名單」為主。
                is_direct = True
                
                airlines_in_option = []
                is_valid_airline = True
                
                for flight in flights:
                    airline_name = flight.get("airline", "未知航空")
                    airlines_in_option.append(airline_name)
                    
                    if not any(allowed.lower() in airline_name.lower() for allowed in allowed_airlines):
                        is_valid_airline = False
                        break
                
                if is_valid_airline and price < best_price:
                    best_price = price
                    best_flight = option
                    best_airlines = list(set(airlines_in_option))

            if not best_flight:
                print(f"在 {origin} 到 {destination} 中，沒有找到符合指定航空公司的航班。")
                return None

            # 取得訂票連結 (Google Flights 搜尋連結)
            booking_link = data.get("search_metadata", {}).get("google_flights_url", "")
            if not booking_link:
                booking_link = f"https://www.google.com/flights?hl=zh-TW#flt={origin}.{destination}.{departure_date}*{destination}.{origin}.{return_date}"

            return {
                "destination": destination,
                "price": best_price,
                "currency": currency,
                "departure_date": departure_date,
                "return_date": return_date,
                "airlines": best_airlines,
                "link": booking_link
            }

        except Exception as e:
            print(f"SerpApi 搜尋發生錯誤 ({destination}): {e}")
            return None
