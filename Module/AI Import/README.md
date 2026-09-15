# Dataset nhận diện vùng bảng Excel

Dự án này chuẩn bị dữ liệu và huấn luyện **một model nhận diện vùng bảng** trong file Excel.
Model không sinh nội dung, không đối chiếu biểu, không mapping vào Document và không cần
`DocType`, `DataField`, `DocumentContent` hay LLM.

Đầu ra của model cho mỗi bảng chỉ gồm năm tọa độ:

```json
{"top": 2, "left": 1, "bottom": 8, "right": 13, "header_bottom": 7}
```

Sau khi mạng neural tìm được vùng, gói model đọc trực tiếp header, value, công thức, style và
merge từ workbook gốc. Kết quả `predict_excel()` đã đầy đủ để backend trả cho giao diện;
model không có cơ hội tự bịa hoặc sửa số liệu. Runtime còn trả `columns[].headerPath` và
`columnCode` để giao diện giữ đúng quan hệ cột cha, cột con.

## Cách tạo dataset

1. Đặt các file `.xlsx`/`.xlsm` vào `Data/Raw`.
2. Mở `BuildDataset.ipynb` bằng kernel Python 3.14.7.
3. Chọn **Run All**.

Notebook tự kiểm tra/cài `openpyxl`, tạo nhãn, chia tập, thêm augmentation và kiểm tra chất
lượng. Sau khi chạy xong chỉ có hai artifact cần dùng:

Cuối notebook có preview trực quan lấy một mẫu từ validation, train, test-id và test-ood.
Preview đọc value/merge trực tiếp từ Raw để mô phỏng kết quả hiển thị nhưng không lưu các
value này vào dataset.

```text
Data/
├── Raw/                    # workbook gốc, không bị sửa
├── dataset.jsonl           # tham chiếu file + nhãn vùng bảng + split + augmentation recipe
└── dataset_report.json     # thống kê và kết quả kiểm tra
```

Mã tạo dataset nằm trong `dataset_builder.py`; dependency duy nhất nằm trong
`requirements.txt`.

## Train model

Chỉ có hai notebook train và một file lõi dùng chung:

```text
Train/
├── train.ipynb             # bản Windows; tự dùng Python 3.12 + PyTorch CPU
├── train_colab.ipynb       # bản Google Colab GPU
└── training_core.py        # model, DataLoader, metric, export và predict_excel()
```

- Máy cá nhân: mở `Train/train.ipynb` bằng kernel Python 3.14.7 và chọn **Run All**.
  Notebook tự tạo `Train/.venv` Python 3.12 vì PyTorch Windows chưa hỗ trợ Python 3.14.
- Colab: chỉ cần đặt toàn bộ `Data` tại `MyDrive/Data`, tải `train_colab.ipynb` lên Colab,
  chọn GPU và **Run All**. Notebook đã nhúng sẵn lõi train và tự kiểm tra checksum trước khi
  chạy; không cần chép thêm file Python lên Drive.

Cell cấu hình đầu tiên của mỗi notebook cho phép chỉnh `EPOCHS`, `BATCH_SIZE`, learning
rate, weight decay, patience, độ lớn model, trọng số ba lớp, thiết bị, worker và các ngưỡng
hậu xử lý. Bản Colab đối chiếu đủ mọi `source_file` trong `dataset.jsonl` với MyDrive trước
khi bắt đầu train và xử lý cả khác biệt chuẩn hóa Unicode trong tên workbook.

Hai bản đều train theo batch/epoch, early stopping theo validation, đánh giá riêng Test-ID và
Test-OOD, vẽ loss/F1/IoU, chọn ngẫu nhiên file test để so sánh kết quả mong đợi với thực tế,
sau đó nạp lại artifact và chạy `predict_excel()`.

Model thành công có tên:

```text
eform_excel_table_extractor_v1.eformmodel
```

Artifact là một file chứa trọng số, cấu hình feature/model, phiên bản dataset, tham số train và
metric. Các file báo cáo/đồ thị nằm trong `Output_Local` hoặc `Output_Colab` tương ứng.

## Một dòng dataset

Các trường cần thiết:

- `source_file`, `sheet_index`: tìm sheet gốc để tạo tensor/feature khi train.
- `workbook_id`, `layout_group`: chống rò rỉ giữa bản sao và đo khả năng tổng quát.
- `sheet_shape`: kích thước sheet.
- `tables`: ground truth gồm `top`, `left`, `bottom`, `right`, `header_bottom`.
- `split`: `train`, `validation`, `test_id` hoặc `test_ood`.
- `augmentation_recipes`: phép dịch hàng/cột, bỏ ngẫu nhiên style/header text; không tạo số
  liệu giả và chỉ gắn cho train.
- `annotation`: nguồn và độ tin cậy của nhãn để kiểm soát chất lượng.

Dataset JSONL không chứa value của các ô và không có DocType. Khi train, hàm
`encode_record(...)` đọc workbook theo yêu cầu rồi biến số, ngày, công thức thành token kiểu
dữ liệu. Text header được chuẩn hóa; các tọa độ nhãn được dịch đúng theo augmentation.

## Nguyên tắc an toàn và đánh giá

- File trùng hoàn toàn được nhận diện bằng SHA-256 và chỉ giữ một workbook canonical.
- Cùng workbook luôn nằm trong một split.
- `test_ood` không chia sẻ `layout_group` với train/validation/test-id.
- `test_id` đo file mới có bố cục quen thuộc; `test_ood` đo bố cục chưa xuất hiện khi train.
- Augmentation chỉ thay vị trí, mức dùng style hoặc che một phần header; không thay value.
- Trường hợp chuẩn `21a` đã được neo nhãn chính xác `A2:M8`, header kết thúc ở hàng 7.

Nhãn còn lại được tự động hóa từ cấu trúc workbook nên `ready_for_training=true` có nghĩa là
dataset hợp lệ về kỹ thuật, không phải lời cam kết độ chính xác model. Trước khi triển khai cần
đánh giá riêng trên `test_id` và `test_ood`; không chỉnh nhãn theo kết quả test.

## Ranh giới trách nhiệm khi chạy thật

```text
Excel gốc
  -> encoder che giá trị thật
  -> model dự đoán 5 tọa độ
  -> kiểm tra tọa độ hợp lệ
  -> code đọc nguyên văn header/value/merge từ Excel gốc
  -> Handsontable preview
  -> người dùng bấm “Nhập dữ liệu”
  -> giao diện cũ xử lý mapping/check nghiệp vụ
```

## Chạy FastAPI và giao diện tích hợp

FastAPI nằm trong `API/main.py`. Model được nạp đúng một lần khi service khởi động, sau đó
mỗi request chỉ chạy inference và đọc lại giá trị từ workbook tạm. API không nhận đường dẫn
file từ client, không cần DocType, DocumentContent hoặc schema biểu đích.

Lần đầu, cài ba dependency web vào đúng môi trường PyTorch hiện có:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) ".uv-cache"
uv pip install --python ".\Train\.venv\Scripts\python.exe" fastapi uvicorn python-multipart
```

Khởi động model service:

```powershell
powershell -ExecutionPolicy Bypass -File ".\API\run_local.ps1"
```

Các endpoint:

- `GET http://127.0.0.1:8010/health`: trạng thái service và model đang nạp.
- `GET http://127.0.0.1:8010/api/eform/model`: thông tin artifact.
- `POST http://127.0.0.1:8010/api/eform/extract`: multipart field `file`, trả workbook preview.

Backend .NET Framework tại `Module/ImportDoucment` gọi endpoint extract bằng multipart và
trả nguyên `aiResult` cho trình duyệt qua `POST /api/import/parse`. Backend không còn yêu cầu
`targetSchemaJson`, `docTypeCode`, `formIndex`, không lưu database ở bước preview và không
mapping dữ liệu.

Mở solution `ImportDoucment.sln`, đặt `ImportDocumentAPI` làm startup project rồi chạy. Trang
chủ hiển thị Handsontable cục bộ, không phụ thuộc CDN. Bảng mở theo toàn bộ số dòng và dùng
thanh cuộn ngoài của trang; các dòng tiêu đề bám mép trên khi cuộn tới và mỗi ô tiêu đề được
giới hạn hai dòng ở lần render đầu. Nội dung đầy đủ vẫn nằm trong tooltip. Khi người dùng bấm
`Nhập dữ liệu`, giao diện phát sự kiện `eform:ai-import-confirmed` với hai phần:

- `detail.selected`: sheet và vùng bảng đang chọn, gồm data, mergeCells, headerRows, columns.
- `detail.workbook`: toàn bộ kết quả từ model để hệ thống chính có thể xử lý nhiều sheet/bảng.

Có thể truyền `window.eformImportContext` trước khi nạp script để nối vào màn hình eForm thật:

```javascript
window.eformImportContext = {
    userId: currentUserId,
    documentId: currentDocumentId,
    templateUrl: templateDownloadUrl,
    onConfirm: function (result) {
        // result.selected là dữ liệu đã xem trước; mapping/check thuộc giao diện biểu.
    }
};
```

Biến môi trường tùy chọn cho service: `EFORM_MODEL_PATH`, `EFORM_DEVICE`,
`EFORM_MAX_UPLOAD_BYTES`, `EFORM_MAX_UNCOMPRESSED_BYTES` và `EFORM_REVIEW_THRESHOLD`.
