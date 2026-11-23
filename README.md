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

## Tích hợp với eform_nq (nút "Nhập file" → "Nhập file Excel" / "Nhập File Excel AI")

Tài liệu chi tiết (kiến trúc, hợp đồng API, kiểm thử): [`Docs/Tích hợp eForm/TAI_LIEU_TICH_HOP_EFORM_NQ_MICROSERVICE.md`](Docs/Tích%20hợp%20eForm/TAI_LIEU_TICH_HOP_EFORM_NQ_MICROSERVICE.md).

ImportDocumentAPI chạy thành một service riêng. Toàn bộ phần import thuộc về service này: gọi AI, kết nối CSDL, lưu bản ghi. eform_nq chỉ làm hai việc: cấp JWT cho user đã đăng nhập, và mở giao diện.

```
Trình duyệt (trang Báo cáo eform_nq http://hoangtv.dev.com, đã đăng nhập; bấm "Nhập file" → "Nhập File Excel AI")
  1. POST /webapi/aiimport/token          → eform_nq (cookie phiên) trả JWT HS256 15 phút + serviceUrl
  2. POST {serviceUrl}/api/import/parse   → ImportDocumentAPI (Bearer JWT, autoSave=false)
       └─ POST http://127.0.0.1:8010/api/eform/extract → AI service (Python)
  3. Người dùng xem và sửa bảng AI đọc được, chọn sheet và ghép vào biểu (dùng luồng validate sẵn có của eform_nq)
  4. POST {serviceUrl}/api/import/save    → ImportDocumentAPI lưu nhật ký vào import_records (không chặn nhập liệu)
  5. eform_nq lưu số liệu báo cáo như khi nhập Excel thường
```

- **Xác thực**: `EformGatewayHandler` bắt buộc có `Authorization: Bearer <jwt>` cho mọi `/api/import/*`, trừ `/api/import/health`. Token phải có `alg=HS256`, `iss=eform_nq`, `aud=eform_import_ai` và còn hạn (cho lệch 60 giây). `userId` và `userName` luôn lấy từ claim `sub` và `name`; giá trị client gửi lên bị bỏ qua.
- **CORS**: chỉ các origin trong `EformAllowedOrigins` được gọi. Preflight `OPTIONS` từ origin lạ bị trả 403.

### Cấu hình

| Nơi | Khóa | Ý nghĩa |
| --- | --- | --- |
| `ImportDocumentAPI/Web.config` | `EformJwtSecret` | Khóa ký JWT (≥ 32 ký tự). **Phải trùng** `AiImportJwtSecret` của eform_nq. |
| | `EformJwtIssuer` / `EformJwtAudience` | Mặc định `eform_nq` / `eform_import_ai`. |
| | `EformAllowedOrigins` | Danh sách origin của eform_nq, phân tách bằng dấu phẩy, hiện là `http://hoangtv.dev.com,http://localhost:64898,...`. |
| | `ImportAuthRequired` | `true` (mặc định). Chỉ đặt `false` khi chạy trang demo độc lập `import-preview`. |
| | `ImportDb` + `EformDataSource` | Kết nối MySQL; bảng `import_records` nằm trong schema `EformDataSource` (mặc định `datamart_eform_nq`). Kết nối luôn dùng `utf8mb4`. |
| `eform_nq/Solution/web.config` | `AiImportServiceUrl` | URL gốc của ImportDocumentAPI mà **trình duyệt** gọi tới, hiện là `http://import_ai_hoangtv.dev.com`. Phải cùng giao thức http/https với eform_nq. |
| | `AiImportJwtSecret` | Trùng `EformJwtSecret`. |
| | `AiImportTokenMinutes` | Thời hạn token, từ 1 đến 60 phút (mặc định 15). |

### Chạy trên IIS local (hoangtv.dev.com / import_ai_hoangtv.dev.com)

1. **CSDL**: chạy `Module/ImportDoucment/Database/20261118_import_records_eform_service.sql` trên schema `datamart_eform_nq`. Script dùng `CREATE TABLE IF NOT EXISTS` nên chạy lại vẫn an toàn.
2. **AI service** (`Module/AI Import/API/main.py`): chạy `powershell -ExecutionPolicy Bypass -File "Module/AI Import/API/run_local.ps1"` (cổng 8010). Script bỏ qua `.venv` hỏng và tự chọn Python có đủ `torch`, `uvicorn`, `fastapi`, `openpyxl`. Kiểm tra `http://127.0.0.1:8010/health` trả `"status":"ready"`. Backend gọi tới `AiUrl` (`http://127.0.0.1:8010/api/eform/extract`).
3. **ImportDocumentAPI**: build `ImportDoucment.sln`; site IIS `import_ai_hoangtv.dev.com` trỏ vào thư mục `ImportDocumentAPI`. Kiểm tra `http://import_ai_hoangtv.dev.com/api/import/health` trả `"status":"ready"`.
4. **eform_nq**: đăng nhập `http://hoangtv.dev.com/`, mở một báo cáo, bấm **Nhập file**. Hộp nhập có hai nút **Nhập file Excel** (cách cũ) và **Nhập File Excel AI**, kèm nhãn trạng thái "Sẵn sàng". Nếu thanh công cụ vẫn hiện nút cũ thì bấm Ctrl+F5.

### Lưu ý triển khai

- Đổi `EformJwtSecret` / `AiImportJwtSecret` trước khi triển khai thật. Không dùng khóa mẫu trong repo.
- Nếu eform_nq chạy https thì ImportDocumentAPI cũng phải chạy https, nếu không trình duyệt sẽ chặn mixed content.
- AI service chỉ nghe ở `127.0.0.1` và chỉ ImportDocumentAPI gọi tới; trình duyệt không gọi thẳng vào AI service.

## Nguyên tắc tích hợp

Không chạy migration thẳng trên production. Không để AI service truy cập database eForm. Không nhận `userId` từ JSON request; lấy từ authentication context. Chỉ gọi commit sau khi người dùng xem preview, hết lỗi blocking và xác nhận.
