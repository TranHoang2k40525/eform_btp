# eForm BTP — AI-assisted Excel Import

Dự án bổ sung quy trình nhập Excel có kiểm soát cho hệ thống eForm hiện hữu. AI chỉ phân tích và đề xuất ánh xạ; quyền sửa, khóa kỳ báo cáo, validation nghiệp vụ và commit dữ liệu vẫn do eForm quyết định.

## Kết quả tuần 2–6

- Phân tích mã nguồn, SQL và ba workbook: xem [`Docs/INITIAL_ANALYSIS_REPORT.md`](Docs/INITIAL_ANALYSIS_REPORT.md).
- Dịch vụ Python/FastAPI phân tích workbook và trả JSON phẳng qua một endpoint `/parse`: `Module/AI Import/Main`.
- Backend .NET Framework 4.8 tách `Domain`, `Application`, `Infrastructure`, `ImportApi` (Web API 2 + Swagger): `Module/Module.ImportDocument`.
- Migration MySQL cô lập dữ liệu import: `Module/Module.ImportDocument/Database`.
- Dataset mẫu, bảy notebook, script fine-tune/evaluate/release gate: `Module/AI Import/Train`.
- Test .NET và Python đã chạy; benchmark cùng smoke-test ba workbook có evidence: xem [`Docs/TEST_REPORT.md`](Docs/TEST_REPORT.md).

## Khởi động nhanh

### Module .NET

```powershell
dotnet build '.\eform_btp.slnx' -c Release
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

Mở `http://127.0.0.1:8010/docs`; API backend Swagger ở `/swagger/ui/index`. Hướng dẫn model ở [`Docs/MODEL_TRAINING.md`](Docs/MODEL_TRAINING.md).

## Nguyên tắc tích hợp

Không chạy migration thẳng trên production. Không để AI service truy cập database eForm. Không nhận `userId` từ JSON request; lấy từ authentication context. Chỉ gọi commit sau khi người dùng xem preview, hết lỗi blocking và xác nhận.
