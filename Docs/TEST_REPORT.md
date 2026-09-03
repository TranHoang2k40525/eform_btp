# Test và smoke evidence

Ngày chốt: 2026-09-03. Theo yêu cầu mới, thư mục test đã được xóa khỏi module; Swagger là cách kiểm thử API chính.

## Backend build

```powershell
dotnet build .\eform_btp.slnx -c Release
```

Kết quả lần cuối: build thành công, 0 warning, 0 error cho `Solution.Domain`, `Module.ImportDocument.Domain`, `Application`, `Infrastructure`, `ImportApi`.

## Python/API

Trước khi dọn thư mục test theo yêu cầu, test suite đã chạy 15/15 pass, coverage 87%. Sau thay đổi, đã compile toàn bộ Python và xác nhận 7 notebook là JSON hợp lệ. Kiểm thử vận hành dùng `GET /health`, `GET /model/version`, và `POST /parse` qua Swagger tại `/docs`.

## Smoke workbook thật

Analyzer read-only đã chạy trên ba workbook được chỉ định, không xuất cell value/ảnh:

| Workbook | Sheet | Visible/hidden | Region | Merge | Thời gian |
|---|---:|---:|---:|---:|---:|
| UBND Phường Láng 01a | 1 | 1/0 | 2 | 19 | 12,06 ms |
| ví dụ 2 | 1 | 1/0 | 1 | 13 | 9,69 ms |
| Tổng hợp biểu mẫu KHTC | 77 | 67/10 | 205 | 3.006 | 7.849,99 ms |

Evidence: `Docs/evidence/workbook-smoke.json`.

## Benchmark synthetic

| Dữ liệu | Tổng thời gian |
|---|---:|
| 1 sheet × 100 hàng | 36,33 ms |
| 1 sheet × 1.000 hàng | 66,64 ms |
| 1 sheet × 10.000 hàng | 419,36 ms |
| 10 sheet × 1.000 hàng | 447,05 ms |

Evidence: `Docs/evidence/benchmark-synthetic.json`, `benchmark-multisheet.json`. Đây là một lượt warm run, chưa phải SLA/p95 production.

## UAT cần làm trên eForm staging

1. User có quyền/kỳ mở và user không quyền/kỳ khóa.
2. File giả, file quá lớn, ZIP không phải XLSX.
3. Merged header, nhiều sheet, formula không được thực thi.
4. Mapping confidence thấp phải hiện review.
5. AI down/timeout trả lỗi rõ ràng, không partial commit.
6. Đối chiếu kết quả với `DocumentContent.SourceData`, `ValueData`, `FormConfig`, `FormStyle` sau khi wire save service thật.

