-- MySQL migration for the isolated import workflow. Review backup/retention policy before production use.
START TRANSACTION;

CREATE TABLE IF NOT EXISTS ImportJob (
    Id CHAR(36) NOT NULL,
    DocumentId BIGINT NOT NULL,
    UserId BIGINT NOT NULL,
    OrganizationId BIGINT NULL,
    Status SMALLINT NOT NULL,
    OriginalFileName VARCHAR(255) NOT NULL,
    StoredFilePath VARCHAR(1000) NOT NULL,
    FileSha256 CHAR(64) NOT NULL,
    FileSize BIGINT NOT NULL,
    AnalysisJson LONGTEXT NULL,
    MappingJson LONGTEXT NULL,
    ValidationJson LONGTEXT NULL,
    ModelVersion VARCHAR(255) NULL,
    CommitReference VARCHAR(255) NULL,
    ErrorCount INT NOT NULL DEFAULT 0,
    WarningCount INT NOT NULL DEFAULT 0,
    Version INT NOT NULL DEFAULT 1,
    CreatedUtc DATETIME(6) NOT NULL,
    UpdatedUtc DATETIME(6) NOT NULL,
    ExpiresUtc DATETIME(6) NULL,
    PRIMARY KEY (Id),
    UNIQUE KEY UX_ImportJob_CommitReference (CommitReference),
    KEY IX_ImportJob_Document_Status (DocumentId, Status),
    KEY IX_ImportJob_User_Created (UserId, CreatedUtc),
    KEY IX_ImportJob_Expiry (ExpiresUtc),
    KEY IX_ImportJob_Hash (FileSha256)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ImportMapping (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    JobId CHAR(36) NOT NULL,
    SourceSheet VARCHAR(255) NULL,
    SourceColumn INT NOT NULL,
    SourceHeader VARCHAR(1000) NOT NULL,
    TargetFieldId VARCHAR(255) NULL,
    Confidence DECIMAL(6,5) NOT NULL,
    Decision VARCHAR(30) NOT NULL,
    ProvenanceJson TEXT NULL,
    UserConfirmed BIT NOT NULL DEFAULT 0,
    PRIMARY KEY (Id),
    UNIQUE KEY UX_ImportMapping_Job_Sheet_Column (JobId, SourceSheet, SourceColumn),
    KEY IX_ImportMapping_Target (TargetFieldId),
    CONSTRAINT FK_ImportMapping_Job FOREIGN KEY (JobId) REFERENCES ImportJob(Id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ImportValidationResult (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    JobId CHAR(36) NOT NULL,
    IsValid BIT NOT NULL,
    ErrorCount INT NOT NULL,
    WarningCount INT NOT NULL,
    RuleSetVersion VARCHAR(100) NULL,
    CreatedUtc DATETIME(6) NOT NULL,
    PRIMARY KEY (Id),
    KEY IX_ImportValidationResult_Job (JobId),
    CONSTRAINT FK_ImportValidationResult_Job FOREIGN KEY (JobId) REFERENCES ImportJob(Id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ImportError (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    JobId CHAR(36) NOT NULL,
    RowNumber INT NULL,
    ColumnNumber INT NULL,
    FieldId VARCHAR(255) NULL,
    Severity VARCHAR(20) NOT NULL,
    Code VARCHAR(100) NOT NULL,
    Message VARCHAR(2000) NOT NULL,
    ValuePreview VARCHAR(500) NULL,
    CreatedUtc DATETIME(6) NOT NULL,
    PRIMARY KEY (Id),
    KEY IX_ImportError_Job_Severity (JobId, Severity),
    KEY IX_ImportError_Job_Row (JobId, RowNumber),
    CONSTRAINT FK_ImportError_Job FOREIGN KEY (JobId) REFERENCES ImportJob(Id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ImportResult (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    JobId CHAR(36) NOT NULL,
    IdempotencyKey CHAR(32) NOT NULL,
    CommitReference VARCHAR(255) NOT NULL,
    InsertedRows INT NOT NULL DEFAULT 0,
    UpdatedRows INT NOT NULL DEFAULT 0,
    CommittedBy BIGINT NOT NULL,
    CommittedUtc DATETIME(6) NOT NULL,
    PRIMARY KEY (Id),
    UNIQUE KEY UX_ImportResult_Job (JobId),
    UNIQUE KEY UX_ImportResult_Idempotency (IdempotencyKey),
    CONSTRAINT FK_ImportResult_Job FOREIGN KEY (JobId) REFERENCES ImportJob(Id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ImportMappingFeedback (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    JobId CHAR(36) NOT NULL,
    SourceHeader VARCHAR(1000) NOT NULL,
    SuggestedFieldId VARCHAR(255) NULL,
    SelectedFieldId VARCHAR(255) NULL,
    Accepted BIT NOT NULL,
    Confidence DECIMAL(6,5) NOT NULL,
    Comment VARCHAR(1000) NULL,
    UserId BIGINT NOT NULL,
    CreatedUtc DATETIME(6) NOT NULL,
    PRIMARY KEY (Id),
    KEY IX_ImportFeedback_Selected (SelectedFieldId, Accepted),
    KEY IX_ImportFeedback_Created (CreatedUtc),
    CONSTRAINT FK_ImportFeedback_Job FOREIGN KEY (JobId) REFERENCES ImportJob(Id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ModelVersion (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    Name VARCHAR(255) NOT NULL,
    Version VARCHAR(100) NOT NULL,
    Sha256 CHAR(64) NULL,
    MetricsJson LONGTEXT NULL,
    IsActive BIT NOT NULL DEFAULT 0,
    CreatedUtc DATETIME(6) NOT NULL,
    PRIMARY KEY (Id),
    UNIQUE KEY UX_ModelVersion_Name_Version (Name, Version),
    KEY IX_ModelVersion_Active (Name, IsActive)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS MappingDictionary (
    Id BIGINT NOT NULL AUTO_INCREMENT,
    FormCode VARCHAR(100) NULL,
    NormalizedSourceHeader VARCHAR(1000) NOT NULL,
    TargetFieldId VARCHAR(255) NOT NULL,
    AliasType VARCHAR(30) NOT NULL DEFAULT 'verified',
    Weight DECIMAL(6,5) NOT NULL DEFAULT 1.00000,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedUtc DATETIME(6) NOT NULL,
    UpdatedUtc DATETIME(6) NOT NULL,
    PRIMARY KEY (Id),
    UNIQUE KEY UX_MappingDictionary_Form_Source_Target (FormCode, NormalizedSourceHeader, TargetFieldId),
    KEY IX_MappingDictionary_Lookup (NormalizedSourceHeader(191), IsActive)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

COMMIT;

