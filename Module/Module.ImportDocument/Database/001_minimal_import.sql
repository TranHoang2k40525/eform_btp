-- Minimal audit/dictionary schema. Raw workbook cells are never stored here.
START TRANSACTION;
CREATE TABLE IF NOT EXISTS ImportAudit (
  Id BIGINT NOT NULL AUTO_INCREMENT, RequestId CHAR(36) NOT NULL, DocumentId BIGINT NOT NULL,
  UserId BIGINT NOT NULL, FileSha256 CHAR(64) NOT NULL, OriginalFileName VARCHAR(255) NOT NULL,
  FileSize BIGINT NOT NULL, ModelVersion VARCHAR(255) NULL, RowCount INT NOT NULL DEFAULT 0,
  Valid BIT NOT NULL DEFAULT 0, ErrorCount INT NOT NULL DEFAULT 0, DurationMs DECIMAL(12,2) NOT NULL DEFAULT 0,
  CreatedUtc DATETIME(6) NOT NULL, PRIMARY KEY (Id), UNIQUE KEY UX_ImportAudit_RequestId (RequestId),
  KEY IX_ImportAudit_Document_Created (DocumentId, CreatedUtc), KEY IX_ImportAudit_FileHash (FileSha256)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS ImportMappingDictionary (
  Id BIGINT NOT NULL AUTO_INCREMENT, FormCode VARCHAR(100) NULL, NormalizedSourceHeader VARCHAR(1000) NOT NULL,
  TargetFieldId VARCHAR(255) NOT NULL, IsActive BIT NOT NULL DEFAULT 1, CreatedUtc DATETIME(6) NOT NULL,
  UpdatedUtc DATETIME(6) NOT NULL, PRIMARY KEY (Id),
  UNIQUE KEY UX_ImportDictionary (FormCode, NormalizedSourceHeader, TargetFieldId),
  KEY IX_ImportDictionary_Lookup (NormalizedSourceHeader(191), IsActive)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
COMMIT;
