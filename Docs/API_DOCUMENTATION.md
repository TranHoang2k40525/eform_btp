# API documentation

## Quy ước chung

- Public eForm API dùng session/token hiện hữu, CSRF cho request thay đổi trạng thái, HTTPS, authorization server-side.
- Python AI API chỉ mở trên private loopback/network; IIS không chuyển tiếp trực tiếp cho browser.
- Mỗi request có `X-Correlation-Id`; response lỗi không trả stack trace/path vật lý.
- JSON UTF-8, thời gian UTC ISO-8601. Giới hạn upload mặc định 25 MiB.

## eForm Import API đề xuất

Base path: `/api/import/jobs`.

| Method/path | Trạng thái yêu cầu | Kết quả |
|---|---|---|
| `POST /` multipart `documentId`, `file` | document editable/unlocked | 201, job Uploaded |
| `POST /{id}/analyze` | Uploaded/Failed | job Analyzed |
| `POST /{id}/map` | Analyzed | job Mapped + mapping preview |
| `POST /{id}/validate` | Mapped | WaitingConfirmation hoặc Mapped nếu lỗi |
| `GET /{id}` | owner/authorized | job metadata |
| `GET /{id}/preview?page=1&pageSize=100` | analyzed+ | Handsontable-compatible page |
| `GET /{id}/errors?page=1&pageSize=100` | mapped+ | error/warning page |
| `POST /{id}/confirm` | WaitingConfirmation, zero error | Confirmed |
| `POST /{id}/commit` | Confirmed | commit result; idempotent |
| `POST /{id}/feedback` | owner/authorized | feedback reference |
| `DELETE /{id}` | pre-commit | Cancelled; file scheduled cleanup |

`userId`, role và permission không được nhận từ body. Controller wrapper lấy từ authentication context rồi gọi facade `ImportJobsController`.

### Preview response

```json
{
  "job_id": "b9e2...",
  "sheet": "Biểu 01",
  "columns": [
    {"source_index": 0, "source_header": "Tên đơn vị", "target_field_id": "organization_name", "confidence": 0.96, "decision": "auto"}
  ],
  "data": [["Đơn vị A", 10]],
  "cell_issues": [{"row": 0, "column": 1, "severity": "warning", "message": "Kiểm tra số liệu"}],
  "page": 1,
  "page_size": 100,
  "total_rows": 1
}
```

`data` là mảng hàng/cột tương thích Handsontable; mọi mapping đi bằng field ID, không phụ thuộc chỉ số column đích.

## Python AI API

Base URL mặc định `http://127.0.0.1:8010/`. Swagger tại `/docs` trong môi trường development.

### GET `/health`

```json
{"status":"ok","version":"0.1.0"}
```

### GET `/model/version`

Trả strategy, service version, embedding model/feature flag và LLM feature flag. .NET lưu snapshot này trong job.

### POST `/analyze`

```json
{"path":"D:\\eform-import\\uploads\\<guid>.xlsx","include_hidden":false,"preview_rows":100}
```

`path` chỉ do .NET server tạo; không expose endpoint này trực tiếp ra Internet. Response gồm hash, sheets, merged ranges, detected regions, headers, preview rows, warning và elapsed.

### POST `/detect-table`

```json
{"path":"D:\\eform-import\\uploads\\<guid>.xlsx","sheet":"Biểu 01","include_hidden":false}
```

### POST `/detect-form`

Cùng request như detect-table; response rank sheet candidates. Khi tích hợp schema catalog, adapter bổ sung form-code ranking dựa trên field coverage.

### POST `/map`

```json
{
  "headers":["Tên cơ quan","Tổng cộng"],
  "sample_rows":[["Đơn vị A",12]],
  "target_fields":[
    {"field_id":"organization_name","label":"Tên đơn vị","aliases":["Tên cơ quan"],"data_type":"string","required":true},
    {"field_id":"total","label":"Tổng số","aliases":["Tổng cộng"],"data_type":"number","required":true}
  ]
}
```

Response mỗi cột gồm target, confidence, decision, provenance và alternatives.

### POST `/validate`

Nhận `headers`, `rows`, `mappings`, `target_fields`, `rules`. Rule hỗ trợ `regex`, `min`, `max`, `in`; required/type lấy từ target field. Rule cross-document/permission vẫn thực hiện trong eForm adapter.

### POST `/feedback`

Chỉ lưu metadata mapping, không lưu raw row. Production .NET endpoint xác thực/authorize rồi proxy một contract đã mask.

## HTTP status

- 400: workbook/contract không hợp lệ.
- 401: chưa xác thực (eForm API).
- 403: không quyền hoặc khóa.
- 404: job không tồn tại/không lộ job của user khác.
- 409: state/version conflict hoặc commit trùng đang xử lý.
- 413: vượt dung lượng.
- 422: validation request schema.
- 502/503/504: AI service lỗi/unavailable/timeout; không commit.

