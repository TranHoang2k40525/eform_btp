# Phân tích source eForm sau khi rà soát toàn bộ

Phạm vi đọc: `C:\Users\hoang\Downloads\eform`, tất cả file `.cs`, `.js`, `.html`, `.css` trong thư mục con; loại `bin`, `obj`, `node_modules`, thư viện, Handsontable/Bootstrap và không đọc ảnh/media.

| Loại | Số file | Dung lượng đọc |
|---|---:|---:|
| C# | 302 | 6.414.209 bytes |
| JavaScript | 362 | 13.493.696 bytes |
| HTML | 2 | 17.280 bytes |
| CSS | 10 | 172.766 bytes |
| Tổng | 676 | 19.862.042 bytes |

## Điểm liên quan import

- `views/document/functions/importExcel.js` là entry FE cho import Excel.
- `DocumentController.cs`, `DocumentHelper.cs`, `SmartFormsController.cs` và các controller báo cáo là backend xử lý document/form.
- `DocumentContent` xuất hiện ở nhiều controller/BLL; các trường dữ liệu cần bảo toàn là `SourceData`, `ValueData`, `FormConfig`, `FormStyle`.
- `SaveDoc` là save path hiện hữu; module mới không ghi trực tiếp vào các bảng này.
- `DefineConfigJson` nằm ở controller/BLL và form/report JavaScript, là nguồn cấu hình rule/field.
- `DocumentPermissions.SuaVanBan` là permission cần adapter; `TaskReportPeriod.IsLock` là điều kiện khóa kỳ cần kiểm tra.
- `postMessage` xuất hiện trong các luồng iframe/client; backend mới không tin message/client để quyết định quyền.
- `XLSX` xuất hiện ở attachment/export/document/form/report paths; module mới chỉ parse upload được authorize.

## Entity/BLL cần dùng làm source of truth

Các nhóm entity/BLL đã rà soát gồm Document, DocumentContent, DocumentCopy, DocumentPermission, TaskReport, TaskReportPeriod, Form, FormDetail, Template, TemplateKey, Report, ReportRule, DataSource, User/Role/Permission và file/attachment. Không sao chép entity legacy vào module; adapter gọi service hiện hữu để tránh hai mô hình dữ liệu cạnh tranh.

## Quyết định tích hợp

1. FE gọi một endpoint Web API `/api/import/parse`.
2. ImportApi lấy user từ `ClaimsPrincipal`, nhận `documentId`, file và `targetSchemaJson`.
3. Application gọi permission/lock adapter trước khi xử lý.
4. Infrastructure lưu file private tạm, gọi AI `/parse`, sau đó xóa file trong `finally`.
5. AI trả JSON phẳng theo `target_field_id`; AI không có DB credential và không gọi `SaveDoc`.
6. Nếu sau này cần ghi form, thêm use case commit riêng gọi đúng save service/transaction của eForm sau bước preview/confirm.

## Rủi ro giữ nguyên từ source

- Import cũ có đường đi first-sheet/index/manual; không dùng lại các giả định đó trong analyzer mới.
- Rule JavaScript/SQL có phụ thuộc form code và cross-document; `/parse` chỉ validation cơ bản, rule nghiệp vụ cuối vẫn do eForm.
- Các workbook có sheet tài khoản/cấu hình nhạy cảm; không đưa vào dataset/log/model.
- Khi mount route vào web app cũ, phải giữ CSRF/auth filter và không để Swagger public.

