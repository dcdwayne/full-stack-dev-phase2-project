import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# 強制載入 .env 檔案中的變數到目前的環境中
load_dotenv(override=True)

# MySQL 的實際連線資訊
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),          
    'password': os.getenv("DB_PASSWORD"),  
    'database': os.getenv("DB_NAME")    
}

def get_db_connection():
    """建立資料庫連線的輔助函式"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"資料庫連線失敗: {e}")
        return None

def get_user_by_email(email: str):
    """透過 Email 尋找使用者 (用於登入驗證、檢查註冊重複)"""
    conn = get_db_connection()
    if conn is None:
        return None
        
    try:
        # dictionary=True 讓回傳的資料格式變成字典 (dict)，方便後續用 key 取值
        cursor = conn.cursor(dictionary=True) 
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone() # 抓取一筆符合的資料
        return user
    except Error as e:
        print(f"查詢失敗: {e}")
        return None
    finally:
        # 確保用完後關閉連線，釋放資源
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_user(name: str, email: str, hashed_password: str) -> bool:
    """在資料庫建立新使用者 (用於註冊)"""
    conn = get_db_connection()
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, hashed_password))
        
        conn.commit() # 記得要 commit 才會真的寫入資料庫
        return True
    except Error as e:
        print(f"寫入失敗: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_order(order_data: dict) -> bool:
    """在資料庫建立新訂單"""
    conn = get_db_connection()
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO orders (
                order_number, user_id, attraction_id, date, time, price, 
                contact_name, contact_email, contact_phone, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'UNPAID')
        """
        val = (
            order_data['order_number'], order_data['user_id'], order_data['attraction_id'],
            order_data['date'], order_data['time'], order_data['price'],
            order_data['contact_name'], order_data['contact_email'], order_data['contact_phone']
        )
        cursor.execute(query, val)
        conn.commit()
        return True
    except Error as e:
        print(f"建立訂單失敗: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_order_status(order_number: str, status: str):
    """更新訂單狀態 (PAID / UNPAID)"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        query = "UPDATE orders SET status = %s WHERE order_number = %s"
        cursor.execute(query, (status, order_number))
        conn.commit()
        return True
    except Error as e:
        print(f"更新訂單狀態失敗: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_payment_record(order_number: str, rec_trade_id: str, status: int, msg: str):
    """儲存 TapPay 的付款結果紀錄"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO payments (order_number, rec_trade_id, status, msg) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (order_number, rec_trade_id, status, msg))
        conn.commit()
        return True
    except Error as e:
        print(f"儲存付款紀錄失敗: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_booking_by_user(user_id: int):
    """付款成功後，清空該使用者的購物車 (booking 表)"""
    try:
        con = mysql.connector.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME")
        )
        cursor = con.cursor()
        
        # 刪除該名使用者的預定紀錄
        sql = "DELETE FROM booking WHERE user_id = %s"
        cursor.execute(sql, (user_id,))
        con.commit()
        
        return True
    except Exception as e:
        print(f"Error in delete_booking_by_user: {e}")
        return False
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'con' in locals() and con.is_connected():
            con.close()