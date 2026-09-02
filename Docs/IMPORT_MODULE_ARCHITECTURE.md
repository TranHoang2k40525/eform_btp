# Kiến trúc Module.ImportDocument

## Ranh giới module

Project target `.NET Framework 4.8`, phù hợp IIS/eForm cũ nhưng dùng SDK-style để build tái lập. Module gồm Domain, Application, Infrastructure, Controllers, Integration, Database và Tests.

```text
ASP.NET Web API hiện hữu
  │ authenticated user + CSRF + multipart stream
  ▼
ImportJobsController facade
  ▼
ImportJobService
  ├─ IDocumentAuthorizationService ──> DocumentPermissions/TaskReportPeriod
  ├─ IImportFileStorage ─────────────> thư mục private ngoài web root
  ├─ IImportJobRepository ───────────> bảng Import*
  ├─ IAiImportClient ────────────────> FastAPI private endpoint
  └─ IImportCommitGateway ───────────> save service eForm hiện hữu
                                          │
                                          └─ DocumentContent SourceData/ValueData/
                                             FormConfig/FormStyle trong transaction
```

## State machine

```text
Uploaded → Analyzing → Analyzed → Mapped → Validating
                                      ↑         │ invalid
                                      └─────────┘
Validating → WaitingConfirmation → Confirmed → Committing → Committed
     │             │                   │             │
     └─ Failed     └─ Cancelled        └─ Cancelled  └─ Failed
```

Mỗi transition tăng `Version`. Repository production phải dùng optimistic update `WHERE Id=@id AND Version=@expectedVersion`. In-memory repository chỉ phục vụ test/demo, không đăng ký ở production.

## Luồng endpoint

1. Upload: lấy user từ authentication context, kiểm tra quyền/khóa, stream vào private storage, hash, tạo job.
2. Analyze: kiểm tra ownership/quyền, gọi Python bằng server-side path trên shared volume.
3. Map: gửi selected region + schema field thật.
4. Validate: kiểm tra dữ liệu và rule; blocking error đưa job về Mapped.
5. Preview: trả headers/rows/mappings/issues theo contract cho Handsontable.
6. Confirm: ghi dấu xác nhận của user khi error count bằng 0.
7. Commit: kiểm tra lại quyền/khóa, gọi save service bằng idempotency key.

## Điểm nối với eForm gốc

`EFormAdapters.cs` định nghĩa hai port bắt buộc:

- `IEFormPermissionPort`: triển khai bằng `DocumentPermissions.SuaVanBan` và trạng thái `TaskReportPeriod.IsLock` thực tế.
- `IEFormDocumentWritePort`: gọi đúng service save hiện hữu để ghi `DocumentContent.SourceData`, `ValueData`, `FormConfig`, `FormStyle` trong một transaction.

Không copy repository nội bộ của eForm vào module. Composition root của web app inject adapter thật. `authenticatedUserId` phải lấy server-side; API không expose nó trong body.

## File lifecycle

- Upload bằng tên GUID và extension allowlist.
- Original filename chỉ là metadata đã `Path.GetFileName`.
- Thư mục upload nằm ngoài web root, ACL chỉ cho app pool và Python service account.
- Job terminal được giữ mặc định 30 ngày cho audit; file gốc nên xóa sau 7 ngày hoặc sớm hơn theo chính sách.
- Cleanup ứng dụng xóa file trước rồi xóa DB; job đang Analyze/Commit không được purge.

## Transaction và idempotency

AI call không nằm trong DB transaction dài. Commit mở transaction ngắn trong save service eForm. `ImportResult.IdempotencyKey` unique; gọi lại job Committed trả reference cũ. Nếu external save thành công nhưng cập nhật job thất bại, reconcile theo idempotency key thay vì save lại.

## Triển khai từng bước

1. Deploy migration + module ở feature flag tắt.
2. Deploy Python service private, kiểm tra health/version.
3. Wire adapters và contract tests.
4. Bật cho nhóm pilot/read-only preview.
5. Bật confirm/commit sau audit log và staging UAT.
6. Rollback bằng tắt feature flag; dữ liệu eForm đã commit không tự động đảo ngược.

