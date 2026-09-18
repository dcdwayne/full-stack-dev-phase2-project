# mcp_server.py
from fastmcp import FastMCP, Context
import mysql.connector
import os
from dotenv import load_dotenv


# 載入環境變數 (確保能讀到 DB 連線資訊)
load_dotenv(override=True)

# 建立 MCP 伺服器實例 (Name 必須是 "台北一日遊" 對應作業規範)
mcp = FastMCP("台北一日遊")

def get_db_connection():
    return mysql.connector.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME")
    )

# --- 1. 搜尋景點工具 ---
@mcp.tool()
def search_attractions(keyword: str) -> dict:
    """
    搜尋台北市景點：透過關鍵字和捷運站名搜尋台北市一日旅遊的景點
    """
    try:
        con = get_db_connection()
        # dictionary=True 可以讓撈出來的資料直接變成 Dict 格式
        cursor = con.cursor(dictionary=True)
        
        # 邏輯與你的 app.py 一致：捷運站完全比對，景點名稱模糊比對
        sql = "SELECT id, name, description, category, mrt FROM attraction WHERE mrt = %s OR name LIKE %s"
        cursor.execute(sql, (keyword, f"%{keyword}%"))
        results = cursor.fetchall()
        
        # 整理成作業規範的 JSON 格式
        data_list = []
        for row in results:
            data_list.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "category": row["category"], # 多提供給 AI 方便排版
                "mrt": row["mrt"]            # 多提供給 AI 方便排版
            })
            
        return {"data": data_list}
        
    except Exception as e:
        print(f"MCP Search Error: {e}")
        # 如果發生錯誤，回傳文件規定的錯誤格式
        return {"error": True}
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()

# --- 2. 預定景點工具 ---
@mcp.tool()
def add_to_cart(attraction_id: int, date: str, time: str, price: int, ctx: Context) -> dict:
    """
    預定景點導覽行程：根據景點編號、日期、時間、價格，預定一個景點導覽行程
    """
    try:
        # 1. 從 HTTP request headers 中抓取 Authorization
        auth_header = None
        try:
            from fastmcp.server.dependencies import get_http_request
            req = get_http_request()
            if req and req.headers:
                auth_header = req.headers.get("authorization")
        except Exception:
            auth_header = None

        if not auth_header or not auth_header.startswith("Bearer "):
            return {"error": True}
            
        token = auth_header.split(" ")[1]
            
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        
        # 2. 根據 Token 找出對應的會員 ID (確認你的資料表是 users 還是 member)
        cursor.execute("SELECT id FROM users WHERE mcp_token = %s", (token,))
        user = cursor.fetchone()
        
        if not user:
            return {"error": True}
            
        user_id = user["id"]
        
        # 3. 將預訂資料寫入 booking 資料表 (與你 app.py 裡的邏輯完全相同)
        sql = """
            INSERT INTO booking (user_id, attraction_id, date, time, price) 
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            attraction_id = VALUES(attraction_id),
            date = VALUES(date),
            time = VALUES(time),
            price = VALUES(price)
        """
        cursor.execute(sql, (user_id, attraction_id, date, time, price))
        con.commit()
        
        # 4. 回傳成功訊息與付款連結 (請替換成你的實際 IP 或網域)
        # 文件要求 Message 中必須包含你的 Booking Page URL
        # 從環境變數讀取網址，如果沒設定預設為 localhost
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
        booking_url = f"{base_url}/booking"
        
        return {
            "ok": True,
            "message": f"台北導覽行程，預定成功，請到 {booking_url} 完成付款。"
        }
        
    except Exception as e:
        print(f"MCP Booking Error: {e}")
        return {"error": True}
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()