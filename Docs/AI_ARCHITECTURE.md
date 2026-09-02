# Kiến trúc AI Import

## Mục tiêu

AI hỗ trợ hiểu workbook và đề xuất ánh xạ vào schema eForm. Nó không quyết định quyền, không sửa rule nghiệp vụ và không ghi database.

## Luồng xử lý

```text
XLSX/XLSM
   │ security scan: extension → signature → size → ZIP ratio → SHA-256
   ▼
WorkbookAnalyzer
   │ sheet metadata, merged ranges, used dimensions
   ▼
Region/Header Detector
   │ row bands, table bounds, multi-row header, preview rows
   ▼
HybridFieldMapper
   ├─ exact/verified alias
   ├─ Vietnamese-normalized fuzzy/token overlap
   └─ optional E5/BGE embedding similarity
   ▼
Confidence Engine
   │ top score + margin → auto/review/unmapped + alternatives + provenance
   ▼
DeterministicValidator
   │ required/type/min/max/regex/in + eForm rule adapter
   ▼
Handsontable-compatible preview → human confirmation → .NET commit gateway
```

## Thành phần

- `security.py`: chống tệp giả và zip bomb, tính hash.
- `excel.py`: parse workbook bằng openpyxl, không chạy macro/external link.
- `detection.py`: detector không phụ thuộc tên file/sheet/hàng cố định.
- `text.py`: Unicode NFKC, chuẩn hóa dấu câu và fold tiếng Việt cho lexical retrieval.
- `mapping.py`: exact/alias/fuzzy, optional Sentence Transformers, confidence/provenance.
- `validation.py`: rule deterministic, tuyệt đối không `eval` biểu thức.
- `service.py`, `api.py`: orchestration và FastAPI contract.

## Chiến lược model

Default runtime là lexical để đảm bảo service khởi động khi chưa có model. Khi `AI_IMPORT_EMBEDDING_ENABLED=true`, model được lazy-load ở lần map đầu tiên. E5 yêu cầu giữ prefix `query:` cho source và `passage:` cho target; bỏ prefix sẽ làm lệch train/serve.

Model 8B không nằm trên critical path. Nếu bổ sung Qwen3 fallback, chỉ gửi header, target catalog đã lọc và vài sample đã mask; response phải là JSON schema, timeout ngắn, không auto-accept kết quả chỉ dựa trên LLM.

## Confidence và provenance

Mỗi mapping chứa:

- source index/header;
- target field ID/label;
- confidence 0..1;
- `decision`: auto/review/unmapped;
- thành phần điểm lexical/semantic và margin;
- tối đa ba alternatives.

Confidence hiện là heuristic calibration. Sau khi có validation set đủ lớn, dùng reliability diagram/expected calibration error để hiệu chỉnh threshold. Không diễn giải 0.90 là “đúng 90%” trước bước calibration này.

## Failure modes

- Không thấy region: trả warning, cho người dùng chọn vùng thủ công.
- Model chưa tải: embedding feature flag tắt hoặc service fail-fast trong health readiness; không âm thầm đổi model.
- AI timeout: job chuyển Failed có thể retry, file không commit.
- Validation lỗi: job quay lại Mapped để chỉnh.
- Hai commit đồng thời: idempotency key + unique index ImportResult.

## Logging/observability

Nên log JSON: correlation ID, job ID, model version, file hash rút gọn, số sheet/row/region, elapsed theo stage, confidence histogram, error code. Không log raw cells, full file path, access token, cookie, email/điện thoại hoặc request body.

Metric vận hành: request latency p50/p95, analyze failure rate, review rate, unmapped rate, validation error rate, user override rate, commit success rate và drift của header vocabulary.

