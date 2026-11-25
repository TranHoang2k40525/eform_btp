# eForm BTP — AI-assisted Excel Import

Dự án bổ sung quy trình nhập Excel có kiểm soát cho hệ thống eForm BTP. Mô hình AI chỉ nhận diện cấu trúc bảng và đề xuất dữ liệu xem trước; quyền sửa, khóa kỳ báo cáo, kiểm tra ràng buộc nghiệp vụ và ghi số liệu chính thức vẫn do eForm quyết định.

## Cấu trúc dự án

- **Dịch vụ AI (`Module/AI Import/`):**
  - `eform_ai/` + `API/main.py`: Gói runtime gọn nhẹ và dịch vụ FastAPI nạp trực tiếp tệp mô hình tự chứa `API/models/eform_excel_table_extractor_v2.eformmodel` (PyTorch TorchScript, tách rời hoàn toàn mã nguồn huấn luyện).
  - `BuildDataset.ipynb`, `dataset_builder.py`, `raw_variant_generator.py`: Quy trình làm sạch dữ liệu gốc và sinh tệp Excel biến thể thật.
  - `Train/train.ipynb`: Sổ tay huấn luyện mô hình PyTorch Thế hệ 2 và xuất gói `.eformmodel`.
  - `tests/test_runtime_and_api.py`: Kiểm thử tự động hợp đồng API và tách biệt Train/Runtime.
- **Dịch vụ tích hợp .NET (`Module/ImportDoucment/`):**
  - Kiến trúc 4 tầng (`Domain`, `Application`, `Infrastructure`, `ImportDocumentAPI` trên .NET Framework 4.8 / Web API 2).
  - Kịch bản khởi tạo bảng nhật ký nhập MySQL: `Module/ImportDoucment/Database/20261118_import_records_eform_service.sql`.
- **Tài liệu & Báo cáo (`Docs/`):**
  - Chuỗi báo cáo thực tập Tuần 1–12, [Tài liệu tích hợp microservice](Docs/Tích%20hợp%20eForm/TAI_LIEU_TICH_HOP_EFORM_NQ_MICROSERVICE.md) và [Báo cáo tổng kết thực tập](Docs/Báo%20cáo%20tổng%20kết/BAO_CAO_THUC_TAP_TOT_NGHIEP_MODULE_AI_IMPORT_EXCEL.docx).

## Tích hợp với eform_nq (nút "Nhập file" → "Nhập file Excel" / "Nhập File Excel AI")

`ImportDocumentAPI` chạy thành một service riêng. Toàn bộ phần import thuộc về service này: xác thực JWT, gọi AI, kết nối CSDL lưu vết. Hệ thống eForm chỉ cấp JWT cho người dùng đã đăng nhập và mở giao diện nhập.

- **Xác thực:** `EformGatewayHandler` bắt buộc có `Authorization: Bearer <jwt>` (HS256) cho mọi yêu cầu `/api/import/*`, trừ `/api/import/health`.
- **CORS:** chỉ các origin nằm trong `EformAllowedOrigins` được phép gọi.

## Chạy trên IIS local (`hoangtv.dev.com` / `import_ai_hoangtv.dev.com`)

1. **CSDL:** chạy `Module/ImportDoucment/Database/20261118_import_records_eform_service.sql` trên schema `datamart_eform_nq`.
2. **AI service:** chạy `powershell -ExecutionPolicy Bypass -File "Module/AI Import/API/run_local.ps1"` (cổng `8010`). Kiểm tra `http://127.0.0.1:8010/health` trả `"status":"ready"`.
3. **ImportDocumentAPI:** build `Module/ImportDoucment/ImportDoucment.sln`; site IIS `import_ai_hoangtv.dev.com` trỏ tới `Module/ImportDoucment/ImportDocumentAPI`. Kiểm tra `http://import_ai_hoangtv.dev.com/api/import/health`.
4. **eForm:** đăng nhập `http://hoangtv.dev.com/`, mở một báo cáo và bấm **Nhập file**.
