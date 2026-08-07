from fastapi import *
from fastapi.responses import FileResponse

from fastapi import Query
from fastapi.responses import JSONResponse
import mysql.connector
import os
from dotenv import load_dotenv

# 強制載入 .env 檔案中的變數到目前的環境中
load_dotenv(override=True)

app=FastAPI()

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")

# ==========================================
# Task 1-2: 取得景點資料列表
# ==========================================
@app.get("/api/attractions", summary="取得景點資料列表", tags = ["Attraction"])
async def get_attractions(
    # 預設 page 從 0 開始比較符合多數前端分頁邏輯，但需配合 API 規格測試
    page: int = Query(0, description="要取得的分頁，每頁 8 筆資料"),
    category: str = Query(None, description="用來完全比對景點分類，沒有給定則不做篩選"),
    keyword: str = Query(None, description="用來完全比對捷運站名稱、或模糊比對景點名稱的關鍵字，沒有給定則不做篩選")
):
    try:
        # 1. 建立資料庫連線
        con = mysql.connector.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME")
        )
        # 設定 dictionary=True，撈出來的資料才會是 Dict 格式，方便轉成 JSON
        cursor = con.cursor(dictionary=True)

        # 2. 動態組合 SQL 語法與參數
        sql = "SELECT * FROM attraction"
        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)
        
        if keyword:
            # 捷運站完全比對，景點名稱模糊比對 (LIKE)
            conditions.append("(mrt = %s OR name LIKE %s)")
            params.extend([keyword, f"%{keyword}%"])

        # 如果有篩選條件，就加上 WHERE
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        # 3. 處理分頁 (Pagination)
        # 為了知道有沒有「下一頁 (nextPage)」，我們刻意多撈一筆 (8 + 1 = 9 筆)
        limit = 9
        offset = page * 8
        sql += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # 執行主查詢
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()

        # 判斷 nextPage
        if len(results) == 9:
            next_page = page + 1
            data = results[:8]  # 只取前 8 筆回傳給前端
        else:
            next_page = None
            data = results

        # 4. 把圖片 (Images) 陣列合併進來
        if data:
            # 抽出這 8 筆景點的 id
            attraction_ids = [row["id"] for row in data]
            
            # 使用 IN 語法一次把這幾個景點的圖片全部撈出來
            format_strings = ','.join(['%s'] * len(attraction_ids))
            img_sql = f"SELECT attraction_id, image_url FROM attraction_image WHERE attraction_id IN ({format_strings})"
            cursor.execute(img_sql, tuple(attraction_ids))
            images_data = cursor.fetchall()

            # 將圖片依據 attraction_id 進行分組
            img_dict = {}
            for img in images_data:
                aid = img["attraction_id"]
                if aid not in img_dict:
                    img_dict[aid] = []
                img_dict[aid].append(img["image_url"])

            # 將整理好的圖片陣列塞回主資料 (data) 中
            for row in data:
                row["images"] = img_dict.get(row["id"], [])

        # 5. 回傳正確格式
        return {
            "nextPage": next_page,
            "data": data
        }

    except Exception as e:
        print(f"Error: {e}") # 在終端機印出錯誤細節方便你 Debug
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )
    finally:
        # 無論成功失敗，確保關閉游標與連線
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()

# ==========================================
# 根據景點編號取得景點資料
# ==========================================
@app.get("/api/attraction/{attractionId}", summary="根據景點編號取得景點資料", tags = ["Attraction"])
async def get_attraction_by_id(
    # 使用 Path 來接收網址路徑上的 {attractionId}
    attractionId: int = Path(..., description="景點編號")
):
    try:
        con = mysql.connector.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME")
        )
        cursor = con.cursor(dictionary=True)

        # 1. 撈取該 ID 的景點主資料
        sql_attraction = "SELECT * FROM attraction WHERE id = %s"
        cursor.execute(sql_attraction, (attractionId,))
        attraction_data = cursor.fetchone() # 因為 ID 是 Primary Key，只會有一筆，用 fetchone 即可

        # 防呆機制：如果資料庫找不到這個 ID 的景點
        if not attraction_data:
            return JSONResponse(
                status_code=400, # 依照 API 文件規範，找不到通常回傳 400
                content={"error": True, "message": "景點編號不正確"}
            )

        # 2. 撈取該景點的所有圖片
        sql_images = "SELECT image_url FROM attraction_image WHERE attraction_id = %s"
        cursor.execute(sql_images, (attractionId,))
        images_data = cursor.fetchall()

        # 將撈出來的圖片整理成一個 List
        image_urls = [img["image_url"] for img in images_data]

        # 3. 組合並回傳正確格式
        attraction_data["images"] = image_urls

        return {
            "data": attraction_data
        }

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()

# ==========================================
# 取得景點分類名稱列表
# ==========================================
@app.get("/api/categories", summary="取得景點分類名稱列表", tags = ["Attraction Category"])
async def get_categories():
    try:
        con = mysql.connector.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME")
        )
        cursor = con.cursor(dictionary=True)

        # 使用 DISTINCT 確保撈出來的分類不會重複，並排除 NULL 的情況
        sql = "SELECT DISTINCT category FROM attraction WHERE category IS NOT NULL"
        cursor.execute(sql)
        results = cursor.fetchall()

        # 將 Dict 轉換成單純字串的 List
        categories = [row["category"] for row in results]

        return {
            "data": categories
        }

    except Exception as e:
        print(f"Error in /api/categories: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()


# ==========================================
# 取得捷運站名稱列表
# ==========================================
@app.get("/api/mrts", summary="取得捷運站名稱列表", tags = ["MRT Station"])
async def get_mrts():
    try:
        con = mysql.connector.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME")
        )
        cursor = con.cursor(dictionary=True)

        # 根據 API 規格，捷運站通常需要依照「周邊景點數量」由多到少排序
        # 因此使用 GROUP BY 將捷運站分組，並用 ORDER BY COUNT(id) DESC 進行降冪排序
        sql = """
            SELECT mrt 
            FROM attraction 
            WHERE mrt IS NOT NULL 
            GROUP BY mrt 
            ORDER BY COUNT(id) DESC
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        # 將 Dict 轉換成單純字串的 List
        mrts = [row["mrt"] for row in results]

        return {
            "data": mrts
        }

    except Exception as e:
        print(f"Error in /api/mrts: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()

# ==========================================
# 網站圖示 (Favicon)
# ==========================================
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # 直接回傳 static 資料夾裡面的圖片
    return FileResponse("static/favicon.ico")