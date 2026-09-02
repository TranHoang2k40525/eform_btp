# Bàn giao nội dung tuần 2 đến tuần 6

Ngày chốt hiện trạng: 2026-09-03.

## Tuần 2 — Khảo sát và thiết kế dữ liệu

Đã hoàn thành:

- kiểm kê kiến trúc nhập Excel hiện tại, luồng save và rule engine;
- kiểm kê 3 workbook, gồm toàn bộ 77 sheet của workbook lớn mà không đọc ảnh;
- phân loại dữ liệu đầu vào, merged header, công thức, sheet ẩn và rủi ro dữ liệu nhạy cảm;
- định nghĩa schema JSONL, lọc email/điện thoại/secret, khử trùng lặp;
- chia train/validation/test theo group để tránh rò rỉ alias/template;
- notebook `01_data_analysis.ipynb`, `02_data_preprocessing.ipynb`.

Minh chứng: `CURRENT_SYSTEM_ANALYSIS.md`, `EXCEL_ANALYSIS.md`, `DATASET_DESIGN.md`, thư mục `AI Import/Data`.

## Tuần 3 — Baseline và phát hiện cấu trúc

Đã hoàn thành:

- baseline exact/alias/fuzzy có chuẩn hóa tiếng Việt;
- phát hiện vùng bảng không phụ thuộc tên sheet/hàng cố định;
- heuristic header dựa trên text ratio, mật độ và bold;
- làm phẳng header nhiều tầng và merged cells;
- kiểm tra allowlist/signature/zip bomb/kích thước workbook;
- notebook `03_baseline_model.ipynb`, `04_structure_detection.ipynb`.

## Tuần 4 — Semantic mapping và API AI

Đã hoàn thành:

- hybrid mapper: lexical + optional multilingual embedding;
- E5-base là model mặc định, BGE-M3 là challenger benchmark;
- confidence, margin, auto/review/unmapped và top alternatives;
- API `/health`, `/analyze`, `/detect-table`, `/detect-form`, `/map`, `/validate`, `/feedback`, `/model/version`;
- validation kiểu dữ liệu/required/min/max/regex/in;
- lưu provenance, không cho AI tự commit.

## Tuần 5 — Module .NET và tích hợp

Đã hoàn thành:

- project .NET Framework 4.8 tương thích eForm;
- state machine Uploaded → Analyze → Map → Validate → Confirm → Commit;
- ownership check, permission/lock check ở đầu luồng và trước commit;
- secure file storage, SHA-256, idempotency key, optimistic version;
- adapter cho `DocumentPermissions.SuaVanBan`, `TaskReportPeriod.IsLock` và save service hiện hữu;
- thiết kế DB, migration và HTTP client đến AI service.

Còn bước phụ thuộc môi trường eForm: hiện thực hai port `IEFormPermissionPort` và `IEFormDocumentWritePort` bằng DI của solution gốc, sau đó thêm Web API route/CSRF theo framework xác thực đang dùng. Adapter cố ý không giả lập logic production.

## Tuần 6 — Đánh giá, bảo mật và triển khai

Đã hoàn thành:

- test module .NET và test suite Python;
- benchmark generator cho 100/1.000/10.000 dòng, tùy chọn nhiều sheet;
- quy trình fine-tune, metric top-k/MRR, no-regression release gate;
- incremental training chỉ dùng feedback đã duyệt;
- hướng dẫn IIS, logging, retention, rollback;
- notebook `05_train_embedding.ipynb`, `06_evaluation.ipynb`, `07_incremental_training.ipynb`.

Chưa chạy tại máy hiện tại:

- Python test/benchmark vì máy không có Python;
- fine-tune/benchmark E5 và BGE-M3 vì không có runtime Python/GPU và người dùng yêu cầu chỉ hướng dẫn;
- integration test ghi thật vào eForm vì workspace này không được phép sửa source gốc/database production.

## Definition of done trước demo

1. Cài Python và chạy toàn bộ test Python.
2. Chép ba workbook đã được phép sử dụng vào `Data/raw` cục bộ (không commit).
3. Chạy analyzer/benchmark, lưu JSON vào evidence của báo cáo.
4. Xuất schema field thật từ eForm, thay catalog example.
5. Wire hai eForm adapter, chạy trên database staging đã backup.
6. Demo với tài khoản có quyền, tài khoản không quyền và kỳ đã khóa.

