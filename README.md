# eForm BTP — AI-assisted Excel Import

Dự án bổ sung quy trình nhập Excel có kiểm soát cho hệ thống eForm hiện hữu. AI chỉ phân tích và đề xuất ánh xạ; quyền sửa, khóa kỳ báo cáo, validation nghiệp vụ và commit dữ liệu vẫn do eForm quyết định.

## Kết quả tuần 2–6

- Báo cáo tiến độ và phân tích nghiệp vụ: xem [`Docs/Bao_cao_tien_do_AI_Import_Excel.md`](Docs/Bao_cao_tien_do_AI_Import_Excel.md).
- Dịch vụ Python/FastAPI phân tích workbook và trả JSON phẳng qua một endpoint `/parse`: `Module/AI Import/Main`.
- Backend .NET Framework 4.8 tách `Domain`, `Application`, `Infrastructure`, `ImportDocumentAPI` (Web API 2 + Swagger): `Module/ImportDoucment`.
- Migration MySQL cô lập dữ liệu import: `Module/ImportDoucment/Database`.
- Dataset mẫu và notebook dựng dữ liệu/fine-tune: `Module/AI Import/Train`.
- Prompt, JSON contract và quy tắc phân cấp: [`Docs/AI_HIERARCHY_MAPPING.md`](Docs/AI_HIERARCHY_MAPPING.md).

## Khởi động nhanh

### Module .NET

```powershell
dotnet build '.\Module\ImportDoucment\ImportDoucment.sln' -c Release
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

Mở `http://127.0.0.1:8010/docs`; API backend Swagger ở `/swagger/ui/index`. Hướng dẫn dựng dataset ở [`Docs/DATASET_BUILDER_GUIDE.md`](Docs/DATASET_BUILDER_GUIDE.md).

Backend gọi `POST http://127.0.0.1:8010/parse`. Multipart `/api/import/parse` cần `file`, `documentId`, `targetSchemaJson`; đồng thời nhận `docTypeCode` và `formIndex`. `targetSchemaJson` là document eForm hiện tại có `DocumentContents/FormConfig`, không phải danh sách field tự đoán.

## Nguyên tắc tích hợp

Không chạy migration thẳng trên production. Không để AI service truy cập database eForm. Không nhận `userId` từ JSON request; lấy từ authentication context. Chỉ gọi commit sau khi người dùng xem preview, hết lỗi blocking và xác nhận.
