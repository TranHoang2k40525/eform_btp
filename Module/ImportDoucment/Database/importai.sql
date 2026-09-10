CREATE DATABASE IF NOT EXISTS importai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE importai;
CREATE TABLE IF NOT EXISTS import_records (
 id INT NOT NULL AUTO_INCREMENT,
 document_id VARCHAR(100) NOT NULL,
 user_id VARCHAR(100) NOT NULL,
 file_name VARCHAR(255) NOT NULL,
 json_data LONGTEXT NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (id), KEY ix_document_id(document_id), KEY ix_user_id(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
