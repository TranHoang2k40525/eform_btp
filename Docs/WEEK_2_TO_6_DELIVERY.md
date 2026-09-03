# Bàn giao tuần 2–6 (phiên bản backend tối giản)

## Tuần 2 — Khảo sát

Đã đọc toàn bộ 676 file `.cs/.js/.html/.css` trong `C:\Users\hoang\Downloads\eform`, loại thư viện/bin/obj/Handsontable/Bootstrap và không đọc ảnh. Các điểm import/entity chính: `DocumentContent`, `SourceData`, `ValueData`, `FormConfig`, `FormStyle`, `DefineConfigJson`, `SaveDoc`, `DocumentPermissions.SuaVanBan`, `TaskReportPeriod.IsLock`, `importExcel.js` và các validator.

Đã kiểm kê ba workbook thật và viết `CURRENT_SYSTEM_ANALYSIS.md`, `EXCEL_ANALYSIS.md`.

## Tuần 3 — Excel analyzer

`Module/AI Import/Main` phát hiện sheet, vùng bảng, header nhiều dòng, merged cells, giới hạn kích thước và trả metadata/preview. Không hard-code tên file/sheet/hàng.

## Tuần 4 — AI

FastAPI có endpoint nội bộ `/parse`: nhận private path + schema, mapping exact/alias/fuzzy + embedding tùy chọn, validation deterministic và trả JSON phẳng. `/health` và `/model/version` chỉ phục vụ vận hành.

Model khuyến nghị là `multilingual-e5-base`; `BGE-M3` là challenger. Không train LLM từ đầu.

## Tuần 5 — Backend

`Module/Module.ImportDocument` đã tổ chức thành bốn project .NET Framework 4.8:

- `Domain` — model thuần;
- `Application` — `ImportPipelineService`;
- `Infrastructure` — secure storage, AI HTTP client, eForm permission adapter, MySql.Data;
- `ImportApi` — Web API 2 controller duy nhất `/api/import/parse`, Swagger, `App_Start`, `Global.asax` (không dùng Program.cs).

Luồng: FE request → ClaimsPrincipal + permission/lock → kiểm tra/lưu file tạm → gọi AI → trả JSON → dọn file.

## Tuần 6 — môi trường chạy

Đã tạo `Web.config`, Swagger registration, MySQL migration `001_minimal_import.sql`, IIS guide, model training guide và evidence benchmark/smoke. Thư mục test đã xóa theo yêu cầu.

Build cuối: `dotnet build .\eform_btp.slnx -c Release` thành công 0 warning/0 error. Analyzer đã chạy trên workbook lớn 77 sheet trong khoảng 7,85 giây.

## Việc cần nối vào eForm thật

1. Implement `ExistingEFormPermissionPort` bằng service quyền/khóa thật.
2. IIS gọi `Global.asax/Application_Start`, khởi tạo composition root và Web API routes.
3. Chạy migration trên staging sau backup.
4. Khởi động FastAPI private, kiểm `/health`/`/model/version`.
5. Gọi Swagger backend bằng tài khoản thật và kiểm tra JSON phẳng trước khi nối save form.
