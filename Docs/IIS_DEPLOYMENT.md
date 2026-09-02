# Triển khai IIS và AI sidecar

## Topology khuyến nghị

- IIS chạy eForm + `Module.ImportDocument` trong app pool hiện hữu hoặc app riêng cùng trust boundary.
- FastAPI chạy Windows Service riêng trên `127.0.0.1:8010` nếu cùng máy; nếu khác máy thì private VLAN + TLS/mTLS.
- Upload folder nằm ngoài IIS web root, ví dụ `D:\eform-import\uploads`.
- IIS app pool identity có read/write upload; Python service chỉ read; không service nào dùng quyền administrator.

## Build/publish .NET

```powershell
dotnet build '.\Module\Module.ImportDocument\Module.ImportDocument.csproj' -c Release
```

Reference DLL vào solution eForm hoặc thêm project vào solution khi merge. Tại composition root:

1. đăng ký SQL repository production;
2. đăng ký `SecureImportFileStorage` với path ngoài web root;
3. đăng ký `EFormDocumentAuthorizationAdapter` với permission port thật;
4. đăng ký `EFormCommitGateway` với save port thật;
5. đăng ký singleton/reused `HttpClient` trỏ FastAPI;
6. map ASP.NET Web API routes, auth filter, CSRF và exception-to-status mapping.

Không dùng `InMemoryImportJobRepository` ở production.

## Cài Python service

Máy server dùng Python 3.11 x64, virtualenv riêng:

```powershell
cd 'D:\apps\eform-ai-import\Main'
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-embedding.txt
```

Biến môi trường production:

```text
AI_IMPORT_UPLOAD_DIR=D:\eform-import\uploads
AI_IMPORT_MAX_FILE_BYTES=26214400
AI_IMPORT_MAX_UNCOMPRESSED_BYTES=209715200
AI_IMPORT_EMBEDDING_ENABLED=true
AI_IMPORT_EMBEDDING_MODEL=D:\models\eform\mapping-e5-v1
AI_IMPORT_MODEL_CACHE=D:\models\eform
AI_IMPORT_LLM_ENABLED=false
```

Tạo Windows Service bằng công cụ được đơn vị phê duyệt (NSSM, WinSW hoặc service wrapper nội bộ), command:

```text
D:\apps\eform-ai-import\Main\.venv\Scripts\python.exe -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010 --workers 1
```

Model embedding chiếm RAM mỗi worker; benchmark trước khi tăng worker. Set working directory là `Main`, service account riêng, auto restart có backoff và log rotation.

## Migration

Không tự chạy từ web startup. DBA chạy migration đã review trên staging rồi production sau backup. Xác nhận MySQL version/charset/type ID. File `002_retention_event.example.sql` mặc định không bật.

## Health/readiness

- Liveness: `/health`.
- Readiness production nên mở rộng để kiểm tra model artifact đã load/hash đúng và upload folder readable.
- eForm startup/monitor kiểm `/model/version`; mismatch version thì tắt feature hoặc chỉ cho preview.

## Security

- FastAPI không public; nếu remote dùng firewall allowlist và TLS.
- Disable hoặc bảo vệ `/docs` production.
- Không đặt DB password trong Python vì service không kết nối DB.
- IIS request limit khớp nhưng không lớn hơn app limit.
- Antivirus/quarantine tệp upload; macro không chạy.
- Structured log mask raw data; Windows ACL cho log/model/upload.

## Rollout

1. Migration staging, deploy AI lexical-only, health/test.
2. Deploy module với feature flag tắt.
3. Pilot preview-only.
4. Bật embedding cho nhóm pilot; đo p95/review/override.
5. UAT commit trên staging snapshot.
6. Bật production theo đơn vị/form code.

## Rollback

- Lỗi AI: tắt AI import flag; import hiện hữu vẫn hoạt động.
- Model regression: trỏ biến model về artifact cũ, restart Python, xác nhận `/model/version`.
- Module lỗi trước commit: cancel/retry job; không xóa vội audit.
- Dữ liệu đã commit sai: dùng quy trình nghiệp vụ/versioning eForm, không chạy SQL xóa tự động.

