-- =============================================================================
-- Service AI Import (microservice canh eform_nq): bang luu vet `import_records`.
--
-- CHAY TREN CSDL MA SERVICE DANG TRO TOI:
--   connection string `ImportDb` trong ImportDocumentAPI/Web.config, NHUNG neu appSettings
--   `EformDataSource` co gia tri thi ImportDbContext doi Database sang gia tri do
--   (hien tai: datamart_eform_nq). Tep nay KHONG co `USE` de chay dung CSDL dang chon.
--
-- THAY DOI GI
--   Tao bang `import_records` dung 6 cot cua entity ImportRecord (Id, DocumentId, UserId,
--   FileName, JsonData, CreatedAt) neu chua co. Ten dang nhap, nguon (EFORM_NQ), sheet, vung,
--   model va du lieu nguoi dung da xac nhan nam trong JsonData.
--   eform_nq KHONG ghi bang nay; chi service AI Import ghi (POST api/import/save).
--
-- Chay lai duoc nhieu lan. Hoan tac: DROP TABLE IF EXISTS `import_records`; (mat lich su nhap AI).
-- =============================================================================

SELECT DATABASE() AS `CSDL dang chay`;

CREATE TABLE IF NOT EXISTS `import_records` (
    `Id`         INT          NOT NULL AUTO_INCREMENT,
    `DocumentId` VARCHAR(100) NOT NULL,
    `UserId`     VARCHAR(100) NOT NULL,
    `FileName`   VARCHAR(255) NOT NULL,
    `JsonData`   LONGTEXT     NOT NULL,
    `CreatedAt`  DATETIME     NOT NULL,
    PRIMARY KEY (`Id`),
    INDEX `IX_import_records_DocumentId` (`DocumentId`),
    INDEX `IX_import_records_CreatedAt` (`CreatedAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kiem tra: ky vong 6 cot.
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'import_records'
 ORDER BY ORDINAL_POSITION;
