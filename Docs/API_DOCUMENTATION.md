# API tối giản: Excel → JSON phẳng

Backend chỉ public một endpoint nghiệp vụ: `POST /api/import/parse`. Swagger UI ở `/swagger/ui/index` khi chạy development.

## Request multipart/form-data

- `file`: `.xlsx` hoặc `.xlsm`, tối đa 25 MiB;
- query `documentId`: số dương;
- field `targetSchemaJson`: schema field do eForm gửi.

```powershell
$schema = '{"fields":[{"field_id":"organization_name","label":"Tên đơn vị","required":true},{"field_id":"total","label":"Tổng số","data_type":"number"}]}'
curl.exe -X POST 'http://localhost:8080/api/import/parse?documentId=123' -F "file=@D:\test\bao-cao.xlsx" -F "targetSchemaJson=$schema"
```

Luồng server: lấy user từ authentication → kiểm `DocumentPermissions.SuaVanBan`/`TaskReportPeriod.IsLock` qua adapter → kiểm tra file → lưu tạm private → gọi AI `/parse` → xóa file tạm → trả JSON.

## Response 200

```json
{
  "file_name":"bao-cao.xlsx", "sha256":"...", "sheet":"Biểu 01",
  "columns":[{"source_header":"Tên đơn vị","target_field_id":"organization_name","confidence":0.96,"decision":"auto"}],
  "rows":[{"organization_name":"Đơn vị A","total":10}], "row_count":1,
  "valid":true, "issues":[], "model_version":"hybrid-v1:lexical", "requires_review":false
}
```

Tên key trong `rows` là `target_field_id`, không phải index cột. `requires_review=true` thì FE phải cho người dùng kiểm tra trước khi lưu.

## Status code

`200` thành công; `400` request/file/schema không hợp lệ; `401` chưa xác thực; `403` thiếu quyền hoặc đã khóa; `413` quá lớn; `502` AI lỗi/timeout. Production không trả stack trace.

## Web API/Swagger registration

```csharp
Global.asax gọi `GlobalConfiguration.Configure(App_Start.WebApiConfig.Register)`.
```

Swagger dùng `Swashbuckle.Core`; khóa Swagger UI hoặc giới hạn admin ở production. Controller không nhận `userId` từ body.

## Internal AI API

FastAPI chỉ bind private loopback: `POST /parse`, `GET /health`, `GET /model/version`. FE không gọi trực tiếp; AI không có DB credential/khả năng commit eForm.
