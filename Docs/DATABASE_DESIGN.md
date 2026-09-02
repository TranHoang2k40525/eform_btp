# Thiết kế cơ sở dữ liệu Import

Migration: `Module/Module.ImportDocument/Database/001_create_import_module.sql`.

## Bảng và vòng đời

| Bảng | Mục đích | Xóa theo job |
|---|---|---|
| `ImportJob` | aggregate root, trạng thái, file hash/path, JSON snapshot, model version | gốc |
| `ImportMapping` | source column → field, confidence, provenance, xác nhận | cascade |
| `ImportValidationResult` | tổng kết mỗi lần validate, rule set version | cascade |
| `ImportError` | lỗi/warning theo row/column/field | cascade |
| `ImportResult` | commit reference, idempotency, row count | giữ cùng job; không cascade |
| `ImportMappingFeedback` | override/accept do người dùng xác nhận | cascade hoặc ẩn danh trước purge tùy chính sách |
| `ModelVersion` | registry metadata và metric | độc lập |
| `MappingDictionary` | alias đã kiểm duyệt | độc lập |

## Chỉ mục quan trọng

- `ImportJob(DocumentId, Status)`: màn hình theo văn bản.
- `ImportJob(UserId, CreatedUtc)`: ownership/history.
- `ImportJob(ExpiresUtc)`: cleanup.
- `ImportJob(FileSha256)`: phát hiện duplicate (không tự từ chối vì cùng file có thể nhập cho document khác).
- `ImportMapping(JobId, SourceSheet, SourceColumn)` unique.
- `ImportError(JobId, Severity)` và `(JobId, RowNumber)` cho preview phân trang.
- `ImportResult(JobId)` và `IdempotencyKey` unique.

## JSON và dữ liệu chuẩn hóa

JSON snapshot hỗ trợ audit/replay, nhưng mapping/error quan trọng được chuẩn hóa để query. Không lưu toàn bộ workbook dạng base64 trong DB. `ValuePreview` phải mask/truncate; tuyệt đối không lưu secret. Nếu MySQL version hỗ trợ JSON và workload đã benchmark, có thể đổi LONGTEXT sang JSON trong migration riêng.

## Concurrency

Mỗi update job dùng:

```sql
UPDATE ImportJob
SET Status = @status, Version = Version + 1, UpdatedUtc = UTC_TIMESTAMP(6)
WHERE Id = @id AND Version = @expectedVersion;
```

Nếu affected rows bằng 0, trả HTTP 409 và reload job. Không dùng last-write-wins.

## Retention

Đề xuất ban đầu:

- file gốc: 7 ngày;
- preview/analysis/error: 30 ngày sau trạng thái terminal;
- commit audit: theo chính sách văn thư hiện hữu;
- feedback đã ẩn danh: tối đa 12 tháng để train;
- secret/PII không có mục đích: không thu thập.

`002_retention_event.example.sql` chỉ là ví dụ, mặc định comment. DBA phải phê duyệt, backup và đảm bảo cleanup file phối hợp trước khi bật event.

## Triển khai migration

1. Backup database và kiểm tra charset/collation hiện hữu.
2. Chạy trên bản sao/staging; ghi thời gian và dung lượng index.
3. Review foreign key type với ID thật của eForm; migration hiện không gắn FK Document/User để tránh sai schema legacy.
4. Chạy integration test và rollback rehearsal.
5. Production trong maintenance window; không dùng tài khoản web app có quyền DDL.

