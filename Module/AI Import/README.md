# AI Import service

FastAPI service phân tích workbook, phát hiện bảng/header, ánh xạ field hybrid, ánh xạ dòng chỉ tiêu phân cấp và validation deterministic. Service không kết nối database eForm.

## Chạy baseline

Từ root workspace với Python 3.11:

```powershell
cd '.\Module\AI Import\Main'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010
```

Mở `/docs`, `/health`, `/model/version`. Các endpoint nghiệp vụ:

- `POST /map`: ánh xạ cột bằng full `header_path` + mã cột, không chỉ dùng nhãn lá như `Tổng số`.
- `POST /hierarchy/prompt`: xem đúng prompt và JSON Schema gửi LLM.
- `POST /hierarchy/map`: ánh xạ hàng `Tổng số → Mục I/II → 1/2 → 1.1/1.2`.
- `POST /parse`: phân tích workbook, trả JSON chuẩn `schema_version=1.0`, `columns`, `row_mappings`, `rows`, `issues`.

`target_schema_json` của `/parse` nhận được cả danh sách `fields` chuẩn hóa và document eForm hiện hữu có `DocumentContents[].FormConfig|FormCode`, `DefineConfigJson`, `SourceData|ValueData`. `form_index` chọn đúng biểu trong document nhiều biểu. Chỉ bind public sau khi có reverse proxy, authentication/service isolation và TLS phù hợp.

## Bật embedding

```powershell
pip install -r requirements-embedding.txt
$env:AI_IMPORT_EMBEDDING_ENABLED='true'
$env:AI_IMPORT_EMBEDDING_MODEL='intfloat/multilingual-e5-base'
python -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010
```

Lần đầu tải model cần mạng. Production trỏ vào artifact nội bộ bất biến.

## Test bằng Swagger/curl

Swagger nội bộ ở `http://127.0.0.1:8010/docs`; kiểm tra `GET /health`, `GET /model/version` và `POST /parse`. API backend Web API dùng Swagger UI `/swagger/ui/index`.

## Cấu hình

Xem `.env.example`. Uvicorn không tự đọc file `.env` nếu chưa truyền `--env-file`; production nên cấu hình biến môi trường qua service manager. `AI_IMPORT_LLM_ENABLED` mặc định `false`. Khi bật, LLM chỉ đề xuất ánh xạ hàng phân cấp bằng structured output. Kết quả luôn qua JSON Schema và hậu kiểm deterministic: ID phải thuộc schema, one-to-one, đúng `kind`, `level` và `parent_ref`. Output lỗi sẽ bị loại và service tự dùng baseline deterministic.

## Giới hạn hiện tại

- `.xls` legacy không được parse; phải chuyển đổi trong tiến trình sandbox được phê duyệt.
- Region detector là heuristic và luôn cần manual fallback cho confidence thấp.
- Validation module hỗ trợ rule cơ bản; rule cross-document/cross-form vẫn do eForm xử lý.
- Mapping semantic lazy-load model; memory/latency phải benchmark trước rollout.
- Các rule tổng cột/tổng dòng, required, readonly và marker `-`, `...`, `…` vẫn là rule deterministic như luồng import Excel hiện hữu; không giao cho LLM.

Prompt, dữ liệu mẫu và contract: `Prompts/`, `Main/examples/` và `../../Docs/AI_HIERARCHY_MAPPING.md`. Bản làm việc sinh trong `Data/Samples/` bị loại khỏi Git theo `.gitignore`.

## Tạo lại catalog field từ snapshot hệ thống cũ

Không được ghép danh sách DocType với danh sách `FormConfig` theo vị trí: một DocType có thể có nhiều `DocumentContents`, làm lệch toàn bộ mã biểu phía sau. Công cụ dưới đây tách từng block `mẫu <DocTypeCode>` và giữ `form_index`:

```powershell
cd '.\Module\AI Import\Main'
python -m ai_import.catalog 'C:\Users\hoang\Downloads\text.txt' '..\Data\Labels\eform_fields.jsonl'
```

Snapshot hiện tại sinh đúng 434 field từ 30 `DocumentContent`. Catalog này chỉ tạo candidate; không tự đặt `verified=true`.

## Gói tool, dataset và huấn luyện

Bản giao nhận tập trung nằm tại `tool/`, không chứa file C#. Xem `tool/BaoCao_AI_Import.html` hoặc `tool/README.md`.

- Chạy `tool/01_BuildDatasetComplete.ipynb` để tạo dataset đã chia train/validation/test.
- Duyệt nhãn tại `tool/work/Labels/mappings.jsonl`; chỉ `human`, `reviewed`, `curated` được đưa vào dataset.
- Chạy `tool/02_TrainModelFromDataset.ipynb` để huấn luyện trên đúng dataset vừa sinh.
- Dataset và model được ghi dưới `tool/artifacts/`; dữ liệu nguồn trong `Data/` không bị notebook sửa.
