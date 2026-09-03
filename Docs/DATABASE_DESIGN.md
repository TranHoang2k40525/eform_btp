# Database tối giản

Migration duy nhất: `Module/Module.ImportDocument/Database/001_minimal_import.sql`.

`ImportAudit` lưu metadata request, hash file, model version, số dòng, lỗi và thời gian; `ImportMappingDictionary` lưu alias đã duyệt. Không lưu raw workbook/cell, token hay secret. Endpoint `/api/import/parse` có thể chạy stateless; audit repository là phần mở rộng tùy chọn.

Chỉ mục chính: request ID unique để chống ghi trùng, `(DocumentId, CreatedUtc)` cho lịch sử và `FileSha256` cho duplicate detection. Chạy migration sau backup/staging review bằng tài khoản DBA, không chạy từ web startup.

Retention đề xuất: audit 30–90 ngày theo chính sách; dictionary giữ theo vòng đời form. Nếu cần lưu file để audit, dùng private object storage riêng và đặt TTL, không đưa vào database.

