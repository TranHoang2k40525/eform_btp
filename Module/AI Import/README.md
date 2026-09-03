# AI Import service

FastAPI service phân tích workbook, phát hiện bảng/header, ánh xạ field hybrid và validation deterministic. Service không kết nối database eForm.

## Chạy baseline

Từ root workspace với Python 3.11:

```powershell
cd '.\Module\AI Import\Main'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010
```

Mở `/docs`, `/health`, `/model/version`. Chỉ bind public sau khi có reverse proxy, authentication/service isolation và TLS phù hợp.

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

Xem `.env.example`. Uvicorn không tự đọc file `.env` nếu chưa truyền `--env-file`; production nên cấu hình biến môi trường qua service manager. `AI_IMPORT_LLM_ENABLED` hiện chỉ là cờ dự phòng và mặc định false; Qwen không nằm trên critical path.

## Giới hạn hiện tại

- `.xls` legacy không được parse; phải chuyển đổi trong tiến trình sandbox được phê duyệt.
- Region detector là heuristic và luôn cần manual fallback cho confidence thấp.
- Validation module hỗ trợ rule cơ bản; rule cross-document/cross-form vẫn do eForm xử lý.
- Mapping semantic lazy-load model; memory/latency phải benchmark trước rollout.

Hướng dẫn train và gọi API đầy đủ: `../../Docs/MODEL_TRAINING.md`.
