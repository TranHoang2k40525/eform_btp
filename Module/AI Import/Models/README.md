# Model registry (không lưu binary vào Git)

Mỗi bản phát hành nằm trong một thư mục bất biến, ví dụ `mapping-e5-v1/`, gồm:

- model/config/tokenizer do Sentence Transformers tạo;
- `training-metadata.json`;
- `evaluation.json`;
- `manifest.json` chứa SHA-256, dữ liệu nguồn, commit mã nguồn và người phê duyệt.

Chỉ cập nhật biến `AI_IMPORT_EMBEDDING_MODEL` sang bản mới sau khi qua `compare_release.py` và kiểm thử tích hợp. Binary model (`*.safetensors`, `*.onnx`) đã bị loại khỏi Git; lưu trong artifact registry nội bộ có kiểm soát truy cập.

