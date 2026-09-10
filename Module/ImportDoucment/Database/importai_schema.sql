CREATE DATABASE IF NOT EXISTS importai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE importai;

CREATE TABLE IF NOT EXISTS import_records (
    Id INT NOT NULL AUTO_INCREMENT,
    DocumentId VARCHAR(100) NOT NULL,
    UserId VARCHAR(100) NOT NULL,
    FileName VARCHAR(255) NOT NULL,
    JsonData LONGTEXT NOT NULL,
    CreatedAt DATETIME NOT NULL,
    PRIMARY KEY (Id),
    INDEX IX_import_records_DocumentId (DocumentId),
    INDEX IX_import_records_CreatedAt (CreatedAt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chạy câu lệnh này nếu bảng đã tồn tại nhưng thiếu DocumentId:
-- ALTER TABLE import_records ADD COLUMN DocumentId VARCHAR(100) NOT NULL DEFAULT '' AFTER Id;
