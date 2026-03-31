CREATE DATABASE IF NOT EXISTS medical_stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medical_stock;

CREATE TABLE user (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE item (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(200) NOT NULL UNIQUE,
    unit_buying_price   DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    unit_selling_price  DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    opening_stock       INT NOT NULL DEFAULT 0,
    current_stock       INT NOT NULL DEFAULT 0,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `transaction` (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    item_id           INT NOT NULL,
    type              VARCHAR(10) NOT NULL CHECK (type IN ('IN', 'OUT')),
    quantity          INT NOT NULL,
    notes             TEXT,
    transaction_date  DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (item_id) REFERENCES item(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Indexes for performance
CREATE INDEX idx_item_name          ON item(name);
CREATE INDEX idx_transaction_item   ON `transaction`(item_id);
CREATE INDEX idx_transaction_date   ON `transaction`(transaction_date);