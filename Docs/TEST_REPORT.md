# Test report

Ngày chạy: 2026-09-03. Môi trường: Windows, .NET SDK 10.0.302, .NET Framework reference assemblies 4.8. Python chưa được cài trên máy này.

## Đã chạy

Command:

```powershell
dotnet build '.\Module\Module.ImportDocument\Tests\Module.ImportDocument.Tests.csproj' --configuration Release
```

Kết quả: build succeeded, 0 warning, 0 error.

Command:

```powershell
& '.\Module\Module.ImportDocument\Tests\bin\Release\net48\Module.ImportDocument.Tests.exe'
```

Kết quả: 8/8 pass:

1. state machine cho phép transition hợp lệ;
2. state machine chặn nhảy thẳng sang Committed;
3. upload tạo job Uploaded;
4. full flow đến Committed;
5. commit gọi lặp lại idempotent;
6. owner isolation;
7. kỳ/document khóa bị từ chối;
8. extension upload allowlist.

## Đã viết nhưng chưa chạy tại máy này

Python test suite:

- analyzer visible/hidden sheet;
- row-band/header/multi-level header detection;
- exact alias mapping và unknown review;
- required/type/min validation;
- fake XLSX/legacy XLS rejection;
- FastAPI health/model version.

Lý do chưa chạy: `python`, `py`, `pip` không tồn tại trong PATH. Đây không phải kết quả pass; cần chạy đúng command trong `MODEL_TRAINING.md` sau khi cài Python.

## Benchmark chưa chạy

`benchmark.py` sinh workbook 100/1.000/10.000 hàng và đo parse/analyze tổng. Không ghi số benchmark giả. Người chạy cần lưu:

- CPU/RAM/môi trường;
- số hàng/sheet/file size;
- total/service elapsed;
- p50/p95 qua tối thiểu 5 lượt sau warm-up;
- lexical vs E5 vs BGE-M3 mapping latency;
- peak memory.

## Tiêu chí UAT

- 100% ca authorization/lock/owner/CSRF đúng.
- 0 duplicate khi commit lại.
- 0 blocking validation error được commit.
- Top-1 >= ngưỡng phê duyệt; top-3 >= 0.95 đề xuất.
- False auto-accept được review riêng, mục tiêu gần 0 trên bộ nghiệp vụ trọng yếu.
- 10.000 dòng không vượt giới hạn timeout/memory đã thống nhất.
- Raw workbook/secret không xuất hiện trong log/artifact Git.

## Hạn chế test hiện tại

- In-memory repository không thay thế test optimistic concurrency trên MySQL.
- Chưa có adapter thật đến permission/save service của source eForm.
- Chưa chạy ba workbook gốc qua Python runtime mới.
- Chưa đo semantic model vì người dùng yêu cầu tự chạy huấn luyện.

