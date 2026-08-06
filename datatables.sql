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

attractionCREATE TABLE attraction_image (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    attraction_id BIGINT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    FOREIGN KEY (attraction_id) REFERENCES attraction(id) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;