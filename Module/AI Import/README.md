# Module AI Import — EForm Excel Table Extractor v2 (PyTorch TorchScript)

Module huấn luyện **mô hình PyTorch đa nhiệm tự chứa (`EFormAxialTableNet`)** và cung cấp dịch vụ FastAPI nạp trực tiếp file model `.eformmodel` mà **không phụ thuộc mã nguồn huấn luyện** và **không cần các rule/regex vá biên cứng**.

## Kiến trúc tách biệt (Train vs Runtime/API)

```text
Module/AI Import/
├── eform_ai/                    # Gói runtime gọn nhẹ cho FastAPI (chỉ cần torch + openpyxl)
│   ├── schema.py                # Đặc tả 60 kênh đặc trưng bất biến vị trí & tên lớp
│   ├── encoder.py               # Chuyển sheet Excel -> Tensor (tối ưu đọc sparse _cells)
│   ├── postprocess.py           # Giải mã hình học thuần từ đầu ra neural (không regex vá biên)
│   ├── extractor.py             # Đọc nguyên văn giá trị/công thức/style/merge từ Excel + guardrail an toàn
│   └── predictor.py             # EFormPredictor: nạp trực tiếp TorchScript .eformmodel qua torch.jit.load()
├── Train/                       # Chỉ dùng khi huấn luyện & đánh giá
│   ├── train.ipynb              # Notebook huấn luyện (hiển thị từng epoch, biểu đồ, stress-test; tự chọn GPU/CPU)
│   ├── model.py                 # Mạng EFormAxialTableNet (Axial Row/Col Context + 5 đầu dự đoán)
│   ├── dataset_cache.py         # Làm sạch nhãn offline + tạo cache tensor (.pt)
│   ├── augmentations.py         # Online augmentation 12+ biến thể thực tế + sheet không có bảng + lệch cột
│   ├── train.py                 # Lõi huấn luyện + xuất 1 file TorchScript tự chứa (.eformmodel)
│   ├── evaluate.py              # Bộ stress-test 13 biến thể trên file unseen (test_id/test_ood)
│   └── Output_Local/            # Kết quả huấn luyện, biểu đồ và file model xuất ra
├── API/
│   ├── main.py                  # FastAPI mỏng (giữ nguyên JSON Schema 2.0 cho .NET & eform_nq)
│   ├── models/                  # Đặt file eform_excel_table_extractor_v2.eformmodel vào đây để phục vụ
│   ├── requirements.txt         # Chỉ cần fastapi, uvicorn, python-multipart, openpyxl, torch
│   └── run_local.ps1            # Khởi động dịch vụ AI tại http://127.0.0.1:8010
└── tests/
    └── test_runtime_and_api.py  # Kiểm thử tự động tách biệt Train/API và contract JSON 2.0
```

## Mô hình học gì thay cho code cứng?

`EFormAxialTableNet` dự đoán đồng thời 5 đầu ra trong một lần forward `O(H × W)`:
1. `cell_logits (4 lớp)`: `outside`, `header_title`, `header_code`, `value`.
2. `table_start_logits (theo hàng)`: nhận diện hàng mở đầu mỗi bảng để tách nhiều bảng chồng nhau.
3. `col_role_logits (5 vai trò cột)`: `outside`, `code_col` (STT), `label_col` (tên dòng), `data_col` (số liệu), `note_col` (ghi chú).
4. `col_mismatch_logits (theo cột)`: so sánh đặc trưng tiêu đề với nội dung cột để phát hiện cột bị lệch (như file B của biểu 11b).
5. `row_type_logits (9 loại hàng)`: `outside_or_header`, `grand_total`, `section`, `item`, `subitem`, `detail`, `data`, `empty`, `unclassified`.

Phần duy nhất được giữ xác định (deterministic) ở `eform_ai/extractor.py` là:
- Đọc nguyên văn giá trị ô, công thức (chỉ mở `data_only=True` khi file thật sự có công thức), `mergeCells`, style và kích thước cột/dòng để **model không bao giờ bịa số liệu**.
- Guardrail an toàn bắt buộc: đếm lỗi công thức Excel (`#REF!`, `#ERROR!...`), cảnh báo thứ tự mã cột bị đảo `(1),(3),(2)` và chặn nhập khi phát hiện lệch cột.

## Tạo dữ liệu sạch & sinh biến thể Excel thật (`BuildDataset.ipynb`)

1. Đặt toàn bộ file gốc `.xlsx`/`.xlsm` trong `Data/Raw/` (không bị sửa đổi).
2. Mở [BuildDataset.ipynb](BuildDataset.ipynb) và chọn **Run All** để:
   - Làm sạch tự động biên bảng gốc (cắt bỏ các dòng ghi chú/chân trang và dòng tiêu đề biểu thừa).
   - Sinh tập file `.xlsx` biến thể thật vào `Data/Raw_Variants/{train,validation,test_id,test_ood}/` (14 kiểu biến thể thực tế, cân bằng trên toàn bộ 28 loại biểu mẫu, kế thừa đúng split gốc để chống rò rỉ dữ liệu).
   - Xuất bộ dữ liệu hợp nhất sạch `Data/dataset.jsonl` + `Data/dataset_report.json` (`ready_for_training: true`).

## Huấn luyện lại bằng Notebook (`.ipynb`)

- Mở `Train/train.ipynb` và chọn **Run All** (`device_name='auto'` tự dùng GPU nếu có hoặc CPU). Notebook hiển thị tiến trình từng epoch, biểu đồ loss/F1/IoU/exact_region, kết quả stress-test 13 biến thể và tự động copy file `eform_excel_table_extractor_v2.eformmodel` sang `API/models/`.

## Chạy FastAPI (chỉ cần có file model)

Đặt file `eform_excel_table_extractor_v2.eformmodel` vào `API/models/` (hoặc cấu hình biến môi trường `EFORM_MODEL_PATH`), sau đó chạy:

```powershell
powershell -ExecutionPolicy Bypass -File ".\API\run_local.ps1"
```

Các endpoint giữ nguyên tương thích 100% với `ImportDocumentAPI` (.NET) và `eform_nq`:
- `GET http://127.0.0.1:8010/health`
- `GET http://127.0.0.1:8010/api/eform/model`
- `POST http://127.0.0.1:8010/api/eform/extract`
