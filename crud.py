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