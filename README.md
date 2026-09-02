# eForm BTP — AI-assisted Excel Import

Dự án bổ sung quy trình nhập Excel có kiểm soát cho hệ thống eForm hiện hữu. AI chỉ phân tích và đề xuất ánh xạ; quyền sửa, khóa kỳ báo cáo, validation nghiệp vụ và commit dữ liệu vẫn do eForm quyết định.

## Kết quả tuần 2–6

- Phân tích mã nguồn, SQL và ba workbook: xem [`Docs/INITIAL_ANALYSIS_REPORT.md`](Docs/INITIAL_ANALYSIS_REPORT.md).
- Dịch vụ Python/FastAPI phân tích workbook, phát hiện bảng, ánh xạ hybrid và validation: `Module/AI Import/Main`.
- Module .NET Framework 4.8 với state machine, upload an toàn, authorization, AI client, idempotent commit và adapter eForm: `Module/Module.ImportDocument`.
- Migration MySQL cô lập dữ liệu import: `Module/Module.ImportDocument/Database`.
- Dataset mẫu, bảy notebook, script fine-tune/evaluate/release gate: `Module/AI Import/Train`.
- Test .NET đã build và chạy; test Python có sẵn nhưng máy hiện tại chưa cài Python: xem [`Docs/TEST_REPORT.md`](Docs/TEST_REPORT.md).

## Khởi động nhanh

### Module .NET

```powershell
dotnet build '.\Module\Module.ImportDocument\Tests\Module.ImportDocument.Tests.csproj' -c Release
& '.\Module\Module.ImportDocument\Tests\bin\Release\net48\Module.ImportDocument.Tests.exe'
```

### AI service (sau khi cài Python 3.11)

```powershell
cd '.\Module\AI Import\Main'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010
```

Mở `http://127.0.0.1:8010/docs`; chạy test theo [`Module/AI Import/README.md`](Module/AI%20Import/README.md). Hướng dẫn train/test model chi tiết ở [`Docs/MODEL_TRAINING.md`](Docs/MODEL_TRAINING.md).

## Nguyên tắc tích hợp

Không chạy migration thẳng trên production. Không để AI service truy cập database eForm. Không nhận `userId` từ JSON request; lấy từ authentication context. Chỉ gọi commit sau khi người dùng xem preview, hết lỗi blocking và xác nhận.

