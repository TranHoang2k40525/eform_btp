# Security checklist

## Upload

- [x] Allowlist `.xlsx`, `.xlsm`; từ chối `.xls` legacy.
- [x] Kiểm tra magic bytes Office Open XML.
- [x] Giới hạn compressed/uncompressed size và ZIP ratio.
- [x] Tên lưu GUID; original name chỉ metadata đã sanitize.
- [x] SHA-256 để audit/duplicate detection.
- [ ] Quét antivirus/quarantine bằng hạ tầng nội bộ trước analyze.
- [ ] Đặt storage ngoài web root với ACL tối thiểu.

## Authentication/authorization

- [x] Service không tin `userId` từ body.
- [x] Ownership check trên job.
- [x] Permission/lock check khi upload/analyze/map/validate/confirm và ngay trước commit.
- [ ] Web API wrapper gắn authentication filter/CSRF/correlation ID hiện hữu.
- [ ] 404 thay vì tiết lộ job của user khác theo policy của hệ thống.

## AI/data

- [x] AI service không có DB credential eForm.
- [x] Không chạy macro, formula hoặc external link.
- [x] Không dùng `eval` cho validation.
- [x] Log design không chứa raw cells/secrets.
- [x] Scrub dataset cơ bản; raw data không commit Git.
- [ ] DLP/PII review và consent/policy cho feedback production.

## Network/deployment

- [ ] FastAPI bind loopback hoặc private VLAN, firewall deny public.
- [ ] TLS/mTLS hoặc service token xoay vòng nếu đi qua máy khác.
- [ ] Secret lấy từ protected configuration, không lưu source/appsettings.
- [ ] Rate limit, request timeout, worker/memory limit.
- [ ] Disable Swagger production hoặc giới hạn truy cập.

## Database/operations

- [x] Idempotency unique key và version column.
- [x] Migration không gắn FK giả vào schema legacy.
- [x] Retention event mặc định không bật.
- [ ] Backup + staging rehearsal + least privilege DB user.
- [ ] Structured audit cho confirm/commit/model version.
- [ ] Reconciliation job cho trạng thái Committing bị gián đoạn.

