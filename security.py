# security.py
import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

# 秘密金鑰 (從環境變數讀取)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_if_not_found")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7 

def get_password_hash(password: str) -> str:
    """將明碼密碼轉換為雜湊值"""
    # bcrypt 要求輸入必須是 bytes 格式，因此先將字串 encode
    pwd_bytes = password.encode('utf-8')
    # 產生隨機鹽巴 (salt)
    salt = bcrypt.gensalt()
    # 進行雜湊
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # 存入 MySQL 前，將 bytes 轉回一般字串 (str)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """比對使用者輸入的明碼密碼與資料庫中的雜湊密碼是否一致"""
    # 將輸入的密碼與資料庫的密碼都轉成 bytes 格式
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # 讓 bcrypt 進行安全比對
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict) -> str:
    """根據使用者的資料簽發 JWT Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """解碼並驗證 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None