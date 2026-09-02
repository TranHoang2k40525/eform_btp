# Gap analysis

## Tóm tắt

Hệ thống hiện hữu đã có import Excel và editor Handsontable nhưng dựa nhiều vào chỉ số cột, cấu hình thủ công và JavaScript hard-code. Module mới lấp khoảng trống bằng phân tích cấu trúc, semantic mapping, confidence/provenance, quy trình xác nhận và audit tách biệt.

| Năng lực | Hiện hữu | Mục tiêu | Phần đã tạo | Việc cần khi tích hợp staging |
|---|---|---|---|---|
| Đọc workbook | ClosedXML first sheet và XLSX phía client | multi-sheet, merged header, nhiều vùng | `WorkbookAnalyzer` | hiệu chỉnh bằng workbook thật |
| Nhận diện form | người dùng chọn/thao tác thủ công | rank ứng viên theo schema | `/detect-form` baseline | thêm catalog field thật |
| Ánh xạ cột | index/manual | exact + alias + fuzzy + embedding | `HybridFieldMapper` | benchmark E5/BGE-M3 |
| Confidence | chưa nhất quán | calibrated + margin + provenance | auto/review/unmapped | hiệu chỉnh threshold |
| Validation | rule SQL/JS và kiểm tra client | deterministic server-side, giữ eForm source of truth | validator + port | chuyển rule thật thành contract |
| Quyền/khóa | có trong hệ thống nhưng chưa thấy kiểm tra inline ở import cũ | kiểm tra mỗi bước nhạy cảm | authorization adapter | wire service thật |
| Commit | import cũ có thể save trực tiếp | preview → confirm → idempotent commit | state machine + gateway | wire save transaction thật |
| Audit | hạn chế | job/mapping/error/feedback/model version | migration 001 | review DBA |
| File security | endpoint cũ chưa thể hiện đủ context | allowlist/signature/size/zip bomb/hash/retention | 2 implementation Python/.NET | antivirus/quarantine nội bộ |
| Model lifecycle | chưa có | version/metric/release/rollback | training scripts + registry convention | artifact registry |
| Deployment | cùng web app | IIS + private Python sidecar | deployment guide | service account/TLS/reverse proxy |

## Rủi ro ưu tiên

1. Sai mapping confidence cao có thể làm sai số liệu hàng loạt. Biện pháp: preview, margin, field uniqueness, validation và xác nhận.
2. Bypass quyền hoặc commit khi kỳ đã khóa. Biện pháp: không tin user ID từ request; kiểm tra lại ngay trước commit.
3. Công thức Excel và external link. Biện pháp: đọc formula như dữ liệu không thực thi, `keep_links=False`, không chạy macro.
4. Zip bomb/tệp giả. Biện pháp: kiểm tra extension, magic bytes, compressed ratio, total uncompressed size.
5. Dữ liệu bí mật lọt vào train/log. Biện pháp: scrub, allowlist field, log metadata, không commit raw workbook/model binary.
6. API contract lệch giữa .NET và Python. Biện pháp: version route, contract test và pin version khi deploy.

## Những gì không nên làm

- Không copy code nguồn gốc sang module rồi sửa song song.
- Không cho FastAPI kết nối MySQL eForm.
- Không dùng `eval` cho rule/formula.
- Không hard-code tên ba workbook, tên sheet hoặc số hàng header vào runtime.
- Không tự động retrain/promote từ feedback chưa duyệt.
- Không chạy migration trên production trước backup, review và staging rehearsal.

