CREATE TABLE attraction (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    address VARCHAR(255),
    transport TEXT,
    mrt VARCHAR(100),
    lat DOUBLE,
    lng DOUBLE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE attraction_image (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    attraction_id BIGINT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    FOREIGN KEY (attraction_id) REFERENCES attraction(id) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE booking (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    attraction_id BIGINT NOT NULL,
    date DATE NOT NULL,
    time VARCHAR(20) NOT NULL,
    price INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (attraction_id) REFERENCES attraction(id)
);

-- 建立訂單資料表 (修正 INT 為 BIGINT)
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL, -- 系統自訂的唯一訂單編號
    user_id BIGINT NOT NULL,                  -- 關聯的使用者 ID (改為 BIGINT)
    attraction_id BIGINT NOT NULL,            -- 關聯的景點 ID (改為 BIGINT)
    date DATE NOT NULL,                       -- 預訂日期
    time VARCHAR(20) NOT NULL,                -- 預訂時間 (morning/afternoon)
    price INT NOT NULL,                       -- 總金額
    contact_name VARCHAR(100) NOT NULL,       -- 聯絡人姓名
    contact_email VARCHAR(100) NOT NULL,      -- 聯絡人信箱
    contact_phone VARCHAR(20) NOT NULL,       -- 聯絡人手機
    status VARCHAR(20) DEFAULT 'UNPAID',      -- 訂單狀態 (UNPAID / PAID)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (attraction_id) REFERENCES attraction(id)
);

-- 建立付款紀錄表 (維持不變，直接執行即可)
CREATE TABLE payments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL,        -- 關聯的訂單編號
    rec_trade_id VARCHAR(50),                 -- TapPay 回傳的交易識別碼 (失敗時可能為空)
    status INT NOT NULL,                      -- TapPay 回傳的狀態碼 (0為成功)
    msg VARCHAR(255),                         -- TapPay 回傳的訊息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_number) REFERENCES orders(order_number)
);